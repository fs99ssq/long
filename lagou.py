#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
import requests
from selenium import webdriver
import pymysql
import pyecharts
from bs4 import BeautifulSoup
import lxml


class Lagou(object):
    def __init__(self):
        self.headers = {
            'Use-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0'}
        self.db = pymysql.connect('localhost', 'root', '3356685jiao', 'lagou2', charset='utf8')
        self.cursor = self.db.cursor()
        print('数据库已链接！')

    def get_res(self):
        url = 'https://www.lagou.com/'
        res = requests.get(url, headers=self.headers)
        return res

    def get_url(self, res):
        theme_new = []
        soup = BeautifulSoup(res.text, 'lxml')
        theme = soup.find_all('div', class_='menu_sub dn')
        theme = str(theme).split('</span>')
        theme_new = []
        content = []
        list_url = []
        kind = []

        server_name = re.compile('<span>(.*)')
        server_url = re.compile(' href="(.*)">(.*)</a>')
        for i in theme:
            theme_new.append(server_name.findall(i))
        for i in range(1, len(theme), 1):
            content_url = server_url.findall(theme[i])
            content.append(content_url)
        print(content[0])
        for i in content[0]:
            list_url.append(i[0])
            kind.append(i[1])
        theme_new.remove([])

        return list_url, kind

    def get_url_page(self, url):
        total = []

        for i in url:
            url_list = []
            page = 1
            while page < 31:
                url = i + str(page)
                page += 1
                url_list.append(url)
            total.append(url_list)
        return total

    def clear_table(self,kind):
        for each in kind:
            sql = 'truncate table `{}`'.format(each)
            self.cursor.execute(sql)
            self.db.commit()

    def get_job(self, url_list, kind):

        br = webdriver.Chrome()
        self.clear_table(kind)

        for k in range(len(url_list)):
            for each in url_list[k]:
                money_new = []
                title_new = []
                format_time_new = []
                location_new = []
                company_name_new = []
                li_b_r_new = []

                br.get(each)
                soup = BeautifulSoup(br.page_source, 'lxml')

                title = soup.find_all('h3')
                money = soup.find_all('span', class_='money')
                format_time = soup.find_all('span', class_='format-time')
                location = soup.find_all('span', class_='add')
                company_name = soup.find_all('div', class_='company_name')
                li_b_r = soup.find_all('div', class_='li_b_r')

                list_tt = [li_b_r, company_name, location, format_time, title, money]
                list_new = [li_b_r_new, company_name_new, location_new, format_time_new, title_new, money_new]

                for i in range(len(list_tt)):
                    for j in list_tt[i]:
                        list_new[i].append(j.text)

                print('录入成功')

                result = []
                for i in range(len(title_new) - 1):
                    param = (title_new[i], money_new[i], location_new[i], format_time_new[i], li_b_r_new[i], company_name_new[i])
                    result.append(param)
                sql = '''insert into `{}` (`title`,`money`,`location`,`format_time`,`li_b_r`,`company_name`) values (%s,%s,%s,%s,%s,%s); '''.format(
                    kind[k])
                self.cursor.executemany(sql, result)
                self.db.commit()

        br.close()
        print('数据录入完成！')

    def initialized_db(self, kind):
        for each in kind:
            try:
                sql = '''
                        create table `{}` (
                            `id` int not null auto_increment,
                            `title`  char(20) not null,
                            `money` char(30) not null,
                            `location` char(30) not null,
                            `format_time` char(20) not null,
                            `li_b_r` text(50) not null,
                            `company_name` text(50) not null,
                            primary key (`id`)
                        );
                        '''.format(each)
                self.cursor.execute(sql)
                self.db.commit()
            except:
                print('表已存在！')
                break
        else:
            print('表创建完成！')

    def get_money(self, kind):
        average = []
        for each in kind:
            sql = 'select id  from `{}` order by id desc'.format(each)
            self.cursor.execute(sql)
            id = self.cursor.fetchmany()
            self.db.commit()
            sql = 'select money from `{}`'.format(each)
            self.cursor.execute(sql)
            money = self.cursor.fetchmany(id[0][0])
            self.db.commit()
            list_b = []
            money_new = []
            check = re.compile('(\d+)[k,K]-(\d+)[k,K]')
            check_new = re.compile('(\d+)[k,K].*')
            money = list(money)
            for i in range(len(money)):
                money[i] = list(money[i])
                if check.findall(money[i][0]):
                    list_b.append(check.findall(money[i][0]))
                else:
                    money[i][0] = check_new.findall(money[i][0])[0] + 'k-' + check_new.findall(money[i][0])[0] + 'k'
                    list_b.append(check.findall(money[i][0]))
            for j in range(len(list_b)):
                money_new.append((int(list_b[j][0][0]) + int(list_b[j][0][1])) / 2 * 1000)
            average_p = round(sum(money_new) / len(money_new), 2)
            average.append(average_p)
        return average

    def map(self, money, key, kind):
        bar = pyecharts.Bar('拉勾各语言平均薪资', height=500, width=1500)
        bar.add('{}'.format(key), kind, money, legend_text_color='green', xaxis_interval=0, xaxis_rotate=21,
                yaxis_rotate=30)
        bar.render(r'E:\github\%s.html' % key)

    def map_new(self, location, count, key):
        bar = pyecharts.Bar('{}职业分布'.format(key), height=500, width=1500)
        bar.add('{}'.format(key), location, count, legend_text_color='green', xaxis_interval=0, xaxis_rotate=21,
                yaxis_rotate=30)
        bar.render(r'E:\github\zhutu\%s.html' % key)

    def map_new_new(self, location, count, key):
        pie = pyecharts.Pie('{}职业分布'.format(key), width=1500, height=800, title_color='blue', title_pos='bottom')
        pie.add('{}'.format(key), location, count, is_random=True, is_label_show=True)
        pie.render(r'E:\github\bingtu\%s.html' % key)

    def get_location(self, kind):
        for lan in kind:
            location_new = []
            total_new = []
            sql = 'select id  from `{}` order by id desc'.format(lan)
            self.cursor.execute(sql)
            id = self.cursor.fetchmany()
            self.db.commit()
            sql = 'select location from `{}`'.format(lan)
            self.cursor.execute(sql)
            location = self.cursor.fetchmany(id[0][0])
            location = list(location)
            self.db.commit()
            for each in location:
                total = []
                b = each[0].split('·')
                b[0] = b[0].replace('[', '')
                b[0] = b[0].replace(']', '')
                if b[0] not in location_new:
                    location_new.append(b[0])
                    total.append(b[0])
                    total.append(1)
                else:
                    for each in total_new:
                        try:
                            if each[0] == b[0]:
                                each[1] += 1
                        except:
                            pass
                total_new.append(total)
            total_new = list(filter(None, total_new))
            location = []
            count = []
            for each in total_new:
                location.append(each[0])
                count.append(each[1])
            self.map_new(location, count, lan)
            self.map_new_new(location, count, lan)
        return '完毕'



    def main(self):

        res = self.get_res()
        list_url, kind = self.get_url(res)
        self.initialized_db(kind)
        url = self.get_url_page(list_url)
        self.get_job(url, kind)
        self.get_location(kind)
        money = self.get_money(kind)
        self.map(money,'平均薪资',kind)


l = Lagou()
l.main()