USE irassh;

create table commands(
    id			int auto_increment primary key,
    command		text,
    impl_type		int default 0,
    prof_type		text
);

create table fake_commands(
    id			int auto_increment primary key,
    command		text,
    fake_output 	text
);

create table cases(
    id			int auto_increment primary key,
    initial_cmd		text,
    cmd_profile		text,
    action		int,
    action_param	text,
    rl_params       text,
    next_cmd		text
);

CREATE TABLE `messages` (
  `id` int(4) NOT NULL auto_increment,
  `message` varchar(250) NOT NULL,
  `country` varchar(12) NOT NULL,
  PRIMARY KEY  (`id`)
) ;

INSERT INTO messages(message, country) VALUES ('This is default msg', 'DEFAULT');