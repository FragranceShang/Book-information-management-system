--建表
CREATE TABLE public.admin_user
(
    uid serial NOT NULL,
    username character varying(11) NOT NULL,
    pwd character varying(164) NOT NULL DEFAULT '00000000',
    uname character varying(11) NOT NULL,
    sex character varying(8) NOT NULL DEFAULT 'unknown',
    age integer NOT NULL,
    super boolean NOT NULL DEFAULT 'false',
    PRIMARY KEY (uid),
    CONSTRAINT sex CHECK (sex in ('unknown','male','female')),
    CONSTRAINT age CHECK (age > 0)
);

CREATE TABLE public.book_list
(
    bid serial NOT NULL,
    bname character varying(11) NOT NULL,
    isbn character(14) NOT NULL,
    author character varying(11) NOT NULL,
    press character varying(11) NOT NULL,
    price double precision NOT NULL,
    amount integer NOT NULL DEFAULT 0,
    PRIMARY KEY (bid),
    CONSTRAINT amount CHECK (amount >=0),
    CONSTRAINT price CHECK (price > 0)
);

CREATE TABLE public.purchase_list
(
    pid serial NOT NULL,
    bid integer NOT NULL,
    price double precision NOT NULL,
    amount integer NOT NULL,
    state character varying(11) NOT NULL DEFAULT 'unpaid',
    PRIMARY KEY (pid),
    FOREIGN KEY (bid)
        REFERENCES public.booklist (bid) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT price CHECK (price > 0),
    CONSTRAINT amount CHECK (amount > 0),
    CONSTRAINT state CHECK (state in ('paid','unpaid','refund','reach'))
);

CREATE TABLE public.bill
(
    billid serial NOT NULL,
    bid integer NOT NULL,
    price double precision NOT NULL,
    "time" timestamp without time zone NOT NULL,
    amount integer NOT NULL,
    "b/s" "char" NOT NULL,
    PRIMARY KEY (billid),
    FOREIGN KEY (bid)
        REFERENCES public.booklist (bid) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT price CHECK (price > 0),
    CONSTRAINT amount CHECK (amount > 0),
    CONSTRAINT "b/s" CHECK ("b/s" in ('b','s'))
);

CREATE TABLE public.reader
(
    rid serial NOT NULL,
    username character varying(11) NOT NULL,
    pwd character varying(164) NOT NULL,
    rname character varying(11) NOT NULL,
    sex character varying(8) NOT NULL DEFAULT 'unknown',
    age integer NOT NULL,
    PRIMARY KEY (rid),
    CONSTRAINT age CHECK (age > 0),
    CONSTRAINT sex CHECK (sex in ('male','female','unknown'))
);

--授权
create role super_admin;
create role common_admin;
create role reader;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO super_admin;
GRANT ALL PRIVILEGES ON bill, booklist, purchasinglist TO common_admin;
grant select on book_list to reader;

grant select, update on admin_user to common_admin;
-- 通过使用行级别的安全策略，确保用户只能访问自己的行
ALTER TABLE admin_user ENABLE ROW LEVEL SECURITY;
CREATE POLICY select_policy ON admin_user for select TO common_admin using(username = current_user);
CREATE POLICY update_policy ON admin_user for update TO common_admin using(username = current_user);

--新增管理员
create function insert_admin_user(username char,pwd varchar,uname char,sex char, age int)
returns void as $$
declare nuid integer;
begin 
	select max(uid)+1 into nuid from admin_user;
	insert into admin_user values (nuid, username, pwd, uname, sex,age,'false');
end;
$$ language plpgsql;

--图书进货函数
--库存中曾经有的书，直接将这本书的ID列入进货清单
create function insert_purchase_list(bid integer,price numeric,amount integer)
returns void as $$
declare npid integer;
begin 
	select max(pid)+1 into npid from purchase_list;
	insert into purchase_list values (npid, bid, price, amount, 'unpaid');
end;
$$ language plpgsql;

--否则需要输入进货书籍的相关信息
create function insert_purchase_list(isbn char,bname varchar,author varchar,press varchar,inprice numeric, outprice numeric,amount integer)
returns void as $$
declare npid integer;
declare nbid integer;
begin 
	select max(pid)+1 into npid from purchase_list;
	select max(bid)+1 into nbid from book_list;
	insert into book_list values (nbid, bname,isbn, author,press, outprice, 0);
	insert into purchase_list values (npid, nbid, inprice, amount, 'unpaid');
end;
$$ language plpgsql;


--图书进货触发器
create function update_purchase_list()
returns trigger as $$
declare inprice numeric;
begin 
	select distinct price into inprice from purchase_list where bid = old.bid;
	if new.amount = 0 and old.amount > 0 then
		PERFORM insert_purchase_list(new.bid,inprice,5);
	end if;
end;
$$ language plpgsql;

create trigger check_purchase_list after update of amount on book_list
	for each row
	execute function update_purchase_list();


--图书付款、到货触发器
create function update_book_bill()
returns trigger as $$
declare nbillid integer;
begin 
	if old.state = 'paid' and new.state = 'reach' then
		update book_list 
		set amount = amount + new.amount
		where bid = new.bid;
	elsif old.state = 'unpaid' and new.state = 'paid' then
		select max(billid)+1 into nbillid from bill;
		insert into bill values(nbillid,new.bid, new.price, localtimestamp(2),new.amount,'b');
	end if;
    return new;
end;
$$ language plpgsql;

create trigger check_book_bill after update of state on purchase_list
	for each row
	execute function update_book_bill();

--图书出售函数
create function sell_book(buyid integer,bamount integer)
returns void as $$
declare nbillid integer;
declare outprice numeric;
declare num integer;
begin 
	select amount into num from book_list where bid = buyid;
	if bamount <= num then
		update book_list set amount = amount - bamount where bid = buyid;
		select max(billid)+1 into nbillid from bill;
		select price into outprice from book_list where bid = buyid;
		insert into bill values (nbillid, buyid,outprice, localtimestamp(2), bamount, 's');
	elsif num = 0 then
			raise notice 'The book is out of stock!Please wait for replenishment.';
	else
		raise notice 'The available stock is insufficient to meet your requirements.Please reduce the purchase quantity!';
	end if;
end;
$$ language plpgsql;

--创建账单视图
create view bill_view as
select *, amount*price as totalmoney
from bill;

--创建搜书索引
create index query_book on book_list(bid)

--初始化
INSERT INTO public.admin_user(
	uid, username, pwd, uname, sex, age, super)
	VALUES (0, '21307130068', 'sjf', 'Mark', 'unknown', 20, True);
INSERT INTO public.admin_user(
	uid, username, pwd, uname, sex, age, super)
	VALUES (1, '20030511', 'cyy', 'Willow', 'female', 18, false);

INSERT INTO public.book_list(
	bid, bname, isbn, author, press, price, amount)
	VALUES (0, '《伊豆的舞女》', '978-7530217795', '川端康成', '岳麓书社', 36.70, 1);

INSERT INTO public.purchase_list(
	pid, bid, price, amount, state)
	VALUES (0, 0, 18.35, 1, 'reach');

INSERT INTO public.bill(
	billid, bid, price, "time", amount, "b/s")
	VALUES (0, 0, 18.35, localtimestamp(2), 1, 'b');

INSERT INTO public.reader(
	rid, username, pwd, rname, sex, age)
	VALUES (0, 'JiaMandi', 'jmd', 'Jmd', 'female', 18);

--检查函数
select insert_purchase_list(0,18.35,1);
select insert_purchase_list('978-7544722803','《树上的男爵》','伊塔洛','译林出版社',22.50,45.00,1);
select insert_admin_user('20020228','hy','Hellen','female',22);

--检查触发器
--图书付款、到货
update purchase_list
set state = 'paid'
where bid = 1 and state = 'unpaid';

update purchase_list
set state = 'reach'
where bid = 1 and state = 'paid';


--检查图书出售函数、进货触发器
select sell_book(1,1);
