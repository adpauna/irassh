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
