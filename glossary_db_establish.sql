drop database if exists `glossary`;
create database `glossary`;
use `glossary`;

drop table if exists `intervals`;
create table `intervals`(
	`mastery_level` tinyint primary key check(`mastery_level` between 0 and 4),
    `next_interval` tinyint not null
);

insert into `intervals` values
	(0, 2),
    (1, 4),
    (2, 8),
    (3, 16),
    (4, 32);

drop table if exists `part_of_speeches`;
create table `part_of_speeches`(
	`pos_id` tinyint primary key,
    `full_name` varchar(20) unique,
    `abbreviation` varchar(5) unique
);

INSERT INTO `part_of_speeches` (`pos_id`, `full_name`, `abbreviation`) VALUES 
	(0, 'Default', 'O.'),
	(1, 'Noun', 'n.'),
	(2, 'Verb', 'v.'),
	(3, 'Adjective', 'adj.'),
	(4, 'Adverb', 'adv.'),
	(5, 'Preposition', 'prep.'),
	(6, 'Phrase', 'phr.'),
	(7, 'Synonym', 'syn.'),
	(8, 'Interjection', 'intj.'),
    (9, 'Conjunction', 'conj.');

drop table if exists `revise_items`;
create table `revise_items`(
	`revise_id` int primary key auto_increment,
    `next_revise_date` date not null,
    `mastery_level` tinyint default 1 check(`mastery_level` between 0 and 5),
    foreign key(`mastery_level`) references `intervals`(`mastery_level`)
);

-- 设置成可null的需要把null加在类型后面
drop table if exists `words`;
create table `words`(
	`spelling` varchar(25) primary key,
    `alias` varchar(25) default null,
    `phonetic` varchar(40) default null,
    `refresh_id` int null default null,
    `respell_id` int null default null,
    foreign key(`refresh_id`) references `revise_items`(`revise_id`) on delete set null,
    foreign key(`respell_id`) references `revise_items`(`revise_id`) on delete set null
);

drop table if exists `meanings`;
create table `meanings`(
	`meaning_id` int primary key,
    `pos_id` tinyint not null default 0,
    `meaning` varchar(250) not null,
    `refresh_id` int null default null, -- 仅当需要用它复习近义词反义词的时候需要
    foreign key(`refresh_id`) references `revise_items`(`revise_id`) on delete cascade,
    foreign key (`pos_id`) references `part_of_speeches`(`pos_id`)
);

drop table if exists `translations`;
create table `translations`(
	`origin` varchar(40) not null,
    `pos_id` tinyint not null default 0,
    `translation` varchar(40) not null,
    foreign key (`pos_id`) references `part_of_speeches`(`pos_id`)
);

drop table if exists `notes`;
create table `notes`(
	`revise_id` int primary key,
    `content` varchar(400) not null,
    foreign key(`revise_id`) references `revise_items`(`revise_id`) on delete cascade
);

drop table if exists `phrases`;
create table `phrases`(
	`phrase` varchar(40) primary key,
    `related_word` varchar(25) default null, -- 如果有相关单词，就说明需要prompt单词来回想搭配；否则需根据中文意思来回想词组
    `refresh_id` int not null,
    foreign key(`refresh_id`) references `revise_items`(`revise_id`) on delete cascade
);

drop table if exists `word_ids`;
create table `word_ids`(
	`spelling` varchar(25) not null,
    `meaning_id` int primary key,
    foreign key(`spelling`) references `words` (`spelling`) on delete cascade,
    foreign key(`meaning_id`) references `meanings`(`meaning_id`) on delete cascade
);

drop table if exists `an_synonyms`;
create table `an_synonyms`(
	`meaning_id` int not null,
    `word` varchar(25) not null,
    `is_synonym` boolean default true,
    foreign key(`meaning_id`) references `meanings`(`meaning_id`) on delete cascade
);

drop table if exists `example_sentences`;
create table `example_sentences`(
	`phrase` varchar(40) default null,
	`meaning_id` int default null,
    `sentence` varchar(150) not null,
    foreign key(`meaning_id`) references `meanings`(`meaning_id`) on delete cascade,
    foreign key(`phrase`) references `phrases`(`phrase`) on delete cascade
);


-- 视图
-- 复习计划总表
drop view if exists `revise_list_all`;
create view `revise_list_all` as
select `revise_id`, `spelling` as 'vocab', `mastery_level`, `next_revise_date`, 'refresh word' as `type`
from `revise_items`
join `words` on `refresh_id` = `revise_id`
union
select `revise_id`, `phrase`, `mastery_level`, `next_revise_date`, 'refresh phrase'
from `revise_items`
join `phrases` on `refresh_id` = `revise_id`
union
select `revise_id`, `words`.`spelling`, `next_revise_date`, `mastery_level`, 'respell'
from `revise_items`
join `words` on `respell_id` = `revise_id`;

-- 重现计划清单
drop view if exists `refresh_list_all`;
create view `refresh_list_all` as
select `revise_id`, `spelling` as 'vocab', `mastery_level`, `next_revise_date`, 'word' as `type`
from `revise_items`
join `words` on `refresh_id` = `revise_id`
union
select `revise_id`, `phrase`, `mastery_level`, `next_revise_date`, 'phrase'
from `revise_items`
join `phrases` on `refresh_id` = `revise_id`;

-- 重拼计划总表
drop view if exists `respell_list_all`;
create view `respell_list_all` as
select `revise_id`, `spelling`, `alias`, `next_revise_date`, `mastery_level`
from `revise_items`
join `words` on `respell_id` = `revise_id`;

-- 今日复习计划总表
drop view if exists `revise_list_today`;
create view `revise_list_today` as
select * from `revise_list_all`
where `next_revise_date` >= curdate();

-- 触发器 与 过程
delimiter $$

-- 触发器
-- 加入新计划时自动插入下次复习日期
drop trigger if exists `set_date_before_insert_item`$$
create trigger `set_date_before_insert_item`
before insert on `revise_items`
for each row 
begin
	declare `_interval_` tinyint;
	select `next_interval` into `_interval_` from `intervals` where `mastery_level` = new.`mastery_level`;
	set new.`next_revise_date` = date_add(curdate(), interval `_interval_` day);
end$$

-- 更新掌握程度时自动计算下次复习日期
-- 由于触发器不能删除正在更新的表，所以需要删除（掌握程度已满）时先给掌握程度设置为空，之后再手动选择掌握程度为空的删除
drop trigger if exists `set_date_before_update_item`$$
create trigger `set_date_before_update_item`
before update on `revise_items`
for each row
begin
	if new.`mastery_level` >= 5 then
		set new.`mastery_level` = null;
	else begin
		declare `_interval_` tinyint;
		select `next_interval` into `_interval_` from `intervals` where `mastery_level` = new.`mastery_level`;
		set new.`next_revise_date` = date_add(curdate(), interval `_interval_` day);
	end;
	end if;
end$$

-- 当复习计划完成时，复习单元删除后需要清理相关表项
-- 仅当单词同时没有复现和重拼的计划时才触发删除; 短语将直接被cascade删除无需手动删; 
drop trigger if exists `delete_words_after_delete_plan`$$
create trigger `delete_words_after_delete_plan`
after delete on `revise_items`
for each row
begin
	delete from `words` where `refresh_id` is null and `respell_id` is null;
end$$

-- 单词删除之前，趁词义id表还在，删去所有对应的单词英文释义，除非该单词释义加入复习计划（同义词）, 没问题
drop trigger if exists `delete_meanings_on_word_delete`$$
create trigger `delete_meanings_on_word_delete`
before delete on `words`
for each row
begin
    delete from `meanings` as m where m.`meaning_id` in
    (select wi.`meaning_id` from `word_ids` as wi where wi.`spelling` = old.`spelling`)
    and m.`refresh_id` is null;
end$$

-- 手动添加cascade: 删除word之后把对应的translation和计划都删掉
drop trigger if exists `delete_translations_on_word_delete`$$
create trigger `delete_translations_on_word_delete`
after delete on `words`
for each row
begin
    delete from `translations` where `origin` = old.`spelling`;
end$$

-- 手动cascade：删除word之后把对应的translation和计划都删掉
drop trigger if exists `delete_translations_on_phrase_delete`$$
create trigger `delete_translations_on_phrase_delete`
after delete on `phrases`
for each row
begin
    delete from `translations` where `origin` = old.`phrase`;
end$$


-- procedure
drop procedure if exists `cancel_refresh_plan_from_word`$$
create procedure `cancel_refresh_plan_from_word` (in str varchar(25))
begin
    update `revise_items` set `mastery_level` = 5
    where `revise_id` in (
        select `refresh_id`
        from `words`
        where `spelling` = str);
end$$

drop procedure if exists `cancel_respell_plan_from_word`$$
create procedure `cancel_respell_plan_from_word` (in str varchar(25))
begin
    update `revise_items` set `mastery_level` = 5
    where `revise_id` in (
        select `respell_id`
        from `words`
        where `spelling` = str);
end$$

drop procedure if exists `cancel_refresh_plan_from_phrase`$$
create procedure `cancel_refresh_plan_from_phrase` (in str varchar(40))
begin
    update `revise_items` set `mastery_level` = 5
    where `revise_id` in (
        select `refresh_id`
        from `phrases`
        where `phrase` = str);
end$$

drop procedure if exists `renew_refresh_plan_for_word`$$
create procedure `renew_refresh_plan_for_word` (in str varchar(25), in note_content varchar(400))
begin
    call `cancel_refresh_plan_from_word`(str);
    insert into `revise_items` () values ();
    update `words` set `refresh_id` = last_insert_id() where `spelling` = str;
    if note_content is not null then
		insert into `notes` values (last_insert_id(), note_content);
    end if;
    delete from `revise_items` where `mastery_level` is null;
end$$

drop procedure if exists `renew_respell_plan_for_word`$$
create procedure `renew_respell_plan_for_word` (in str varchar(25), in alias varchar(25))
begin
    call `cancel_respell_plan_from_word`(str);
    insert into `revise_items` () values ();
    update `words` set `respell_id` = last_insert_id() where `spelling` = str;
    delete from `revise_items` where `mastery_level` is null;
    if alias is not null then
		update `words` set `alias` = alias where `spelling` = str;
    end if;
end$$

drop procedure if exists `delete_word`$$
create procedure `delete_word`(in str varchar(25))
begin
	call `cancel_respell_plan_from_word`(str);
    call `cancel_refresh_plan_from_word`(str);
    delete from `revise_items` where `mastery_level` is null;
end$$
delimiter ;