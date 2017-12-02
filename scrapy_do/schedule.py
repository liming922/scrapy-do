#-------------------------------------------------------------------------------
# Author: Lukasz Janyst <lukasz@jany.st>
# Date:   02.12.2017
#
# Licensed under the 3-Clause BSD License, see the LICENSE file for details.
#-------------------------------------------------------------------------------

import dateutil.parser
import sqlite3
import uuid

from scrapy_do.utils import TimeStamper
from datetime import datetime
from enum import Enum


#-------------------------------------------------------------------------------
class Status(Enum):
    SCHEDULED = 1
    PENDING = 2
    RUNNING = 3
    CANCELED = 4
    SUCCESSFUL = 5
    FAILED = 6


#-------------------------------------------------------------------------------
class Actor(Enum):
    SCHEDULER = 1
    USER = 2


#-------------------------------------------------------------------------------
class Job:

    status = TimeStamper('_status')
    actor = TimeStamper('_actor')
    schedule = TimeStamper('_schedule')
    project = TimeStamper('_project')
    spider = TimeStamper('_spider')
    duration = TimeStamper('_duration')

    #---------------------------------------------------------------------------
    def __init__(self, status=None, actor=None, schedule=None,
                 project=None, spider=None, timestamp=None, duration=None):
        self.identifier = str(uuid.uuid4())
        self._status = status
        self._actor = actor
        self._schedule = schedule
        self._project = project
        self._spider = spider
        self.timestamp = timestamp or datetime.now()
        self._duration = duration


#-------------------------------------------------------------------------------
class Schedule:
    """
    A persistent database of jobs
    """

    #---------------------------------------------------------------------------
    def __init__(self, database=None, table='schedule'):
        self.database = database or ':memory:'
        self.table = table
        # http://twistedmatrix.com/trac/ticket/4040
        self.db = sqlite3.connect(self.database,
                                  check_same_thread=False,
                                  detect_types=sqlite3.PARSE_DECLTYPES)

        query = "CREATE TABLE IF NOT EXISTS {table} (" \
                "identifier VARCHAR(36) PRIMARY KEY, " \
                "status INTEGER NOT NULL, " \
                "actor INTEGER NOT NULL, " \
                "schedule VARCHAR(255), " \
                "project VARCHAR(255) NOT NULL, " \
                "spider VARCHAR(255) NOT NULL, " \
                "timestamp DATETIME NOT NULL, " \
                "duration INTEGER" \
                ")"
        query = query.format(table=self.table)
        self.db.execute(query)

    #---------------------------------------------------------------------------
    def get_jobs(self, job_status):
        """
        Retrieve a list of jobs with a given status
        """
        query = "SELECT * FROM {table} WHERE status=? ORDER BY timestamp DESC"
        query = query.format(table=self.table)
        response = self.db.execute(query, (job_status.value, ))
        jobs = []
        for x in response:
            job = Job(status=Status(x[1]), actor=Actor(x[2]), schedule=x[3],
                      project=x[4], spider=x[5],
                      timestamp=dateutil.parser.parse(x[6]),
                      duration=x[7])
            job.identifier = x[0]
            jobs.append(job)
        return jobs

    #---------------------------------------------------------------------------
    def add_job(self, job):
        """
        Add a job to the database
        """
        query = "INSERT INTO {table}" \
                "(identifier, status, actor, schedule, project, spider, " \
                "timestamp, duration) " \
                "values (?, ?, ?, ?, ?, ?, ?, ?)"
        query = query.format(table=self.table)
        self.db.execute(query, (job.identifier, job.status.value,
                                job.actor.value, job.schedule, job.project,
                                job.spider, job.timestamp, job.duration))
        self.db.commit()

    #---------------------------------------------------------------------------
    def commit_job(self, job):
        """
        Modify an existing job
        """
        query = "REPLACE INTO {table}" \
                "(identifier, status, actor, schedule, project, spider, " \
                "timestamp, duration) " \
                "values (?, ?, ?, ?, ?, ?, ?, ?)"
        query = query.format(table=self.table)
        self.db.execute(query, (job.identifier, job.status.value,
                                job.actor.value, job.schedule, job.project,
                                job.spider, job.timestamp, job.duration))
        self.db.commit()

    #---------------------------------------------------------------------------
    def remove_job(self, job_id):
        """
        Remova a job from the database
        """
        query = "DELETE FROM {table} WHERE identifier=?"
        query = query.format(table=self.table)
        self.db.execute(query, (job_id,))
        self.db.commit()
