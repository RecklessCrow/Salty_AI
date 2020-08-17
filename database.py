from sqlite3 import connect


def create_connection(db_file=':memory:'):
    return connect(db_file)


def drop_tables(conn):
    c = conn.cursor()
    c.execute(
        """
        drop table if exists authors
        drop table if exists characters
        drop table if exists matches
        """
    )


def create_tables(conn):
    c = conn.cursor()
    c.execute(
        """
        create table if not exists authors (
            id integer primary key,
            name text not null,
            num_wins integer,
            num_matches integer,
            win_rate float generated always as (num_wins / num_matches) virtual
        );
        
        create table if not exists characters (
            id integer primary key,
            name text not null,
            author text,
            num_wins integer,
            num_matches integer,
            win_rate float as (num_wins / num_matches),
            x int,
            y int,
            foreign key (author) references authors (name),            
        );
        """
    )
