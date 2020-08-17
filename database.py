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
            num_wins integer default 0,
            num_matches integer default 1,
            win_rate float generated always as (num_wins / num_matches) virtual
        );
        
        create table if not exists characters (
            id integer primary key,
            name text not null,
            author text,
            num_wins integer default 0,
            num_matches integer default 1,
            win_rate float as (num_wins / num_matches),
            x integer default 0,
            y integer default 0,
            foreign key (author) references authors (name),            
        );
        
        create table if not exists matches (
            match_num int primary key,
            red int not null,
            blue int not null,
            winner int not null,
            foreign key (red) references characters (id),
            foreign key (blue) references characters (id),
        );
        """
    )
