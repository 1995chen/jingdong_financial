# -*- coding: UTF-8 -*-


"""
dependencies: Migration component
"""

import logging
import os
import re
from typing import Any, Callable, List, Optional

from sqlalchemy import Boolean, Column, Integer, String, func

from infra.dependencies.rdb import MainRDB
from infra.exceptions import HandlerNotCallableException
from infra.models.base import Base, BaseModel

logger = logging.getLogger(__name__)


__all__ = [
    "Migration",
    "get_migration_instance",
]


class MigrationLog(BaseModel):
    """
    Model required for database migration
    """

    __tablename__ = "migration_logs"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="primary key")
    project = Column(String(32), nullable=False, default="", index=True)
    version = Column(Integer, nullable=False, index=True)
    script = Column(String(64), nullable=False, default="")
    success = Column(Boolean, nullable=False, default="")


class Migration:
    """
    Service data migration script
    """

    def __init__(
        self,
        main_rdb: MainRDB,
        project: str,
        workspace: str,
    ) -> None:
        """
        init method
        database_uri: database uel
        project: project name
        workspace: migrate script workspace
        [data migration scripts are in the workspace/migrations/ directory]
        """
        self.engine = main_rdb.engine
        self.main_rdb = main_rdb
        self.project = project
        self.script_path = os.path.join(workspace, "migrations")
        if not os.path.exists(self.script_path):
            os.mkdir(self.script_path)
        self.do_init_data_handler: Optional[Callable] = None

    def set_do_init_data_handler(self, handler: Callable) -> None:
        """
        Set the initialization data handler
        :param handler:
        """
        if not callable(handler):
            raise HandlerNotCallableException(f"{type(self).__name__}.set_do_init_data_handler")
        self.do_init_data_handler = handler

    def _generate_table(self) -> None:
        """
        create table
        """
        Base.metadata.create_all(bind=self.engine)
        logger.info("generate_table success")

    def _drop_table(self) -> None:
        """
        drop table
        :return:
        """
        Base.metadata.drop_all(bind=self.engine)
        logger.info("drop_table success")

    def _init_data(self, *args: Any, **kwargs: Any) -> None:
        """
        init data
        """
        # Execute user-defined handler
        if callable(self.do_init_data_handler):
            logger.info("call user defined init handler")
            self.do_init_data_handler(*args, **kwargs)
        # Add migrate record
        with self.main_rdb.get_session() as session:
            _migrate = MigrationLog(
                version=0, script="sys_init", success=True, project=self.project
            )
            session.add(_migrate)
            session.commit()
        self._add_migration_log()
        logger.info("init_data success!")

    def is_inited(self) -> bool:
        """
        Returns whether the service has been initialized
        """
        with self.main_rdb.get_session() as session:
            _migration_log: MigrationLog = (
                session.query(MigrationLog).filter(MigrationLog.project == self.project).first()
            )
        return _migration_log is not None

    def _add_migration_log(self) -> None:
        """
        This method will only create a migrate record and will not execute the script
        """
        _project: str = self.project
        with self.main_rdb.get_session() as session:
            # Each time you recreate the database, you need to restore
            # all the current migration scripts to the device
            regexp = re.compile(r"migration_prod_(\d+).py$")
            max_version = (
                session.query(MigrationLog)
                .filter_by(success=True, project=_project)
                .with_entities(func.max(MigrationLog.version))
                .first()[0]
            )
            max_version = max_version if max_version is not None else -1
            matches = {}
            migration_list: List[str] = os.listdir(self.script_path)
            for f in migration_list:
                match = regexp.match(f)
                if match is not None:
                    matches[f] = int(match.group(1))
            files = sorted(
                [x for x in migration_list if matches.get(x) is not None], key=lambda x: matches[x]
            )
            for f in files:
                version = matches[f]
                if version > max_version:
                    _migrate = MigrationLog(
                        version=version, script=f, success=True, project=_project
                    )
                    session.add(_migrate)
                    session.commit()
        logger.info("success add migrate log")

    def __execute_migration_scripts(self) -> None:
        """
        execute migration scripts
        """
        _project: str = self.project
        with self.main_rdb.get_session() as session:
            # Find the migrate script that meets the naming rules
            regexp = re.compile(r"migration_prod_(\d+).py$")
            failed_fp = "/tmp/migration.failed"

            migrations_logs = (
                session.query(MigrationLog).filter(MigrationLog.project == _project).all()
            )

            # Execution success record
            success_versions = sorted(
                {_i.version for _i in filter(lambda _x: _x.success, migrations_logs)}
            )
            # Execution failed record, and this version did not succeed later
            fail_versions = sorted(
                {
                    _i.version
                    for _i in filter(
                        lambda _x: not _x.success and _x.version not in success_versions,
                        migrations_logs,
                    )
                }
            )

            # The maximum version number of the migration that has been successfully executed.
            max_success_version = -1
            if success_versions:
                max_success_version = max(success_versions)

            # Migration file name and version number mapping
            matches = {}
            migration_file_list = os.listdir(self.script_path)
            for f in migration_file_list:
                match = regexp.match(f)
                if match is not None:
                    matches[f] = int(match.group(1))

            # Migration number with no execution record
            executed_versions = success_versions + fail_versions
            no_executed_versions = sorted(
                [v for v in matches.values() if v not in executed_versions]
            )

            logger.info(f"max successful version: {max_success_version}")
            logger.info(f"successful versions: {success_versions}")
            logger.info(f"failed versions: {fail_versions}")
            logger.info(f"non-executed versions: {no_executed_versions}")

            with open(failed_fp, "w", encoding="utf-8") as fp:
                line = str(fail_versions)
                fp.write(line)

            files = sorted(
                filter(lambda x: matches.get(x) is not None, migration_file_list),
                key=lambda x: matches[x],
            )
            for f in files:
                version = matches[f]
                if version > max_success_version:
                    migrate_func = os.path.splitext(os.path.basename(f))[0]
                    # noinspection PyBroadException
                    try:
                        migrations = __import__(f"migrations.{migrate_func}")
                        migrations_prod = getattr(migrations, migrate_func)
                        migrations_prod.do()
                        success = True
                    except Exception as e:
                        logger.error(f"migration failed for {version}", exc_info=True)
                        success = False
                        raise e
                    finally:
                        _migrate = MigrationLog(
                            version=version, script=f, project=_project, success=success
                        )
                        session.add(_migrate)
                        session.commit()

            logger.info("Migrate successfully")

    def do_migrate(self, *args: Any, **kwargs: Any) -> None:
        """
        Execute the migrate operation
        When the service is not initialized, only the initialization
        script is called, and no migrate script is executed.
        Therefore, the initialization script must be updated
        as the service version changes.
        """
        self._generate_table()
        _is_inited: bool = self.is_inited()
        logger.info(f"init state is {_is_inited}")
        if not _is_inited:
            self._init_data(*args, **kwargs)
            return
        self.__execute_migration_scripts()


def get_migration_instance(main_rdb: MainRDB, project: str, workspace: str) -> Migration:
    """
    :param main_rdb: MainRDB instance
    :param project: project name
    :param workspace: migration workspace
    :return: Migration instance
    """
    return Migration(
        main_rdb,
        project,
        workspace,
    )
