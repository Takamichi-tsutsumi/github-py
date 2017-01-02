from peewee import *
from datetime import datetime as dt
database = PostgresqlDatabase('research', **{})


def str2dt(tstr):
    return dt.strptime(tstr, '%Y-%m-%dT%H:%M:%SZ')


class MultipleChoicesError(Exception):
    pass


class UnknownField(object):
    def __init__(self, *_, **__): pass


class BaseModel(Model):
    class Meta:
        database = database


class Developers(BaseModel):
    created_at = DateField(null=True)
    followers = IntegerField(null=True)
    followings = IntegerField(null=True)
    github = IntegerField(db_column='github_id', unique=True)
    login = CharField()
    prev_downloaded = BooleanField(default=False)

    @classmethod
    def from_raw(cls, raw_data):
        developer = cls(
            github=raw_data["id"],
            login=raw_data["login"]
        )
        return developer

    @classmethod
    def create_from_raw(cls, raw_contributors):
        for r in raw_contributors:
            if Developers.select().where(Developers.github == r["id"]).count() == 0:
                Developers.from_raw(r).save()

    class Meta:
        db_table = 'developers'


class Repositories(BaseModel):
    age = IntegerField()
    commits = IntegerField()
    created_at = DateField(null=True)
    degree_centrality = FloatField(null=True)
    firm_involvement = BooleanField()
    full_name = CharField(unique=True)
    github = IntegerField(db_column='github_id', unique=True)
    internal_cohesion = FloatField(null=True)
    manager = ForeignKeyField(db_column='manager_id', null=True, rel_model=Developers, to_field='github')
    size = IntegerField(null=True)

    @classmethod
    def from_raw(cls, raw_data):
        repo = cls(
            full_name=raw_data["full_name"],
            github=raw_data["id"],
            size=raw_data["size"],
            firm_involvement=(raw_data["owner"]["type"] == "Organization"),
            age=(str2dt(raw_data["pushed_at"]) - str2dt(raw_data["created_at"])).days,
            created_at=raw_data["created_at"]
            )
        return repo

    class Meta:
        db_table = 'repositories'


class Involvement(BaseModel):
    commit_count = IntegerField(null=True)
    developer = ForeignKeyField(db_column='developer_id', null=True, rel_model=Developers, to_field='github')
    repository = ForeignKeyField(db_column='repository_id', null=True, rel_model=Repositories, to_field='github')

    @classmethod
    def create_from_raw(cls, raw_contributors, repo_id):
        print("Insert involvement")
        for c in raw_contributors:
            if cls.select().where(cls.developer == c["id"]).where(cls.repository == repo_id).count() == 0:
                cls.create(
                    developer=c["id"],
                    repository=repo_id,
                    commit_count=c["contributions"]
                )
        print("Done")

    class Meta:
        db_table = 'involvement'
        indexes = (
            (('developer', 'repository'), True),
        )
