# encoding=utf-8
'''
Created on 2013-6-25

@author: tangyi
'''

import sys, string, os, re, time
import urllib2
import logging
from Queue import Queue
from Queue import Empty
from threading import Thread
import threading
from optparse import OptionParser 
import BeautifulSoup


"""
    设置系统的默认编码为utf8
    如果不设置，会造成很多url由于编码问题无法打开
"""
reload(sys) 
sys.setdefaultencoding('utf8')


"""
    线程槽类，每个实例对象负责执行具体的任务
"""
class TreadPoolSlot(Thread):
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.idle = True
        self.logger = logging.getLogger(__name__)
        self.start()

    def run(self):
        while True:
            try:
                func, args, kwargs = self.tasks.get(True,5)#假设５秒后还没有任务，则所有任务已经执行完毕，退出？
            except Empty:
                break
            self.idle = False#得到任务，开始工作
            try:
                func(*args, **kwargs)
            except Exception, e:
                self.logger.error('%s %s' % (e.__class__.__name__, e))
            self.tasks.task_done()# 这个任务已经完成
            self.idle = True

"""
    线程池类，负责管理所有工作线程，向任务队列中添加任务
"""
class TreadPool(object):
    def __init__(self, num):
        """num: 线程池中的线程数."""
        self.tasks = Queue()
        self.pool = []
        for i in range(num):
            self.pool.append(TreadPoolSlot(self.tasks))

    def spawn(self, func, *args, **kwargs):
        """
            向队列中添加任务
        """
        self.tasks.put((func, args, kwargs))

    def joinall(self):
        """等待队列中所有的任务完成."""
        self.tasks.join()
        """等待所有线程结束."""
        for thread in self.pool:
            thread.join()

    def undone_tasks(self):
        """
            注意：非线程安全
        """
        r = 0
        for thread in self.pool:
            if not thread.idle:
                r += 1
        if r:
            r += self.tasks.qsize()
        return r

"""
    一只爬虫
"""
class Spider(object):

    def __init__(self,
                 url,
                 depth,
                 threads,
                 maxsize):
        """i初始化爬虫，但不会自动开始运行！
        url: 从url指定的位置开始爬行
        depth: 爬行深度
        threads: 开启的线程数
        maxsize: 获取的资源上限，达到上限爬虫停止
        """
        self.logfile='sys_run.log'
        self.logger = self.get_logger(self.logfile)#系统运行日志
        self.resource_log=open('Resource.txt',"wb")#爬取到的资源链接文件
        self.url_pattern = self.compile_url_pattern()
        self.url=url
        self.depth = depth
        self.maxsize=maxsize
        self.threads=threads
        self.count=0 #资源计数
        self.tasks_queue = Queue()
        self.pool = TreadPool(threads)
        self.progress_urls = []#process uniq url

    def compile_url_pattern(self):
        """
            匹配hao123站下的资源，可以稍作改进，匹配self.url指定的站点资源链接　
        """
        self.url_pattern = re.compile(r'http://.*hao123.*\.com.*',re.I)
        return self.url_pattern
    
    def GetPage(self,url):
        try: 
            fp = urllib2.urlopen(url)
            result = fp.read()
        except Exception, e:
            self.logger.error(
                'url %s is unreachable. Exception %s %s' %
                (url, e.__class__.__name__, e))
            result=None
        fp.close()
        return result
    
    def get_all_links(self,content):
        """
            得到几种标签的url
        """
        a_tag=self.get_atag_links(content)
        img_tag=self.get_imgtag_links(content)
        link_tag=self.get_linktag_links(content)
        script_tag=self.get_scriptag_links(content)
        all_links=a_tag+img_tag+link_tag+script_tag
        
        return all_links
    
    def crawl_page(self, url, depth):
        """
            爬取页面，获得资源链接
        """
        if depth <= 1:# if depth is done then stop
            return
        if self.count >= self.maxsize:
            return
        result = self.GetPage(url)
        if not result:
            return
        self.logger.info('get content from %s done' % url)
        links = self.get_all_links(result)
        links = self.filter_links(links)#去掉不符合要求的url        
        for link in links:
            self.tasks_queue.put((link, depth - 1))# put links into queue

    def filter_links(self, links):
        """
           过滤链接
        """
        filtered_links=[]
        for url in links:
            if self.url_pattern.match(url):
                filtered_links.append(url)
        return filtered_links
        

    def get_atag_links(self, content):
        """得到a标签中的链接."""
        soup = BeautifulSoup.BeautifulSoup(content)
        links = []
        for link in soup('a'):
            for attr in link.attrs:
                if attr[0] == 'href':
                    links.append(attr[1].strip())
        return links

    def get_imgtag_links(self, content):
        """得到img标签中的链接."""
        soup = BeautifulSoup.BeautifulSoup(content)
        links = []
        for link in soup('img'):
            for attr in link.attrs:
                if attr[0] == 'src':
                    links.append(attr[1].strip())
        return links
    
    def get_linktag_links(self, content):
        """得到link标签中的链接."""
        soup = BeautifulSoup.BeautifulSoup(content)
        links = []
        for link in soup('link'):
            for attr in link.attrs:
                if attr[0] == 'href':
                    links.append(attr[1].strip())
        return links
    
    def get_scriptag_links(self, content):
        """得到script标签中的链接."""
        soup = BeautifulSoup.BeautifulSoup(content)
        links = []
        for link in soup('script'):
            for attr in link.attrs:
                if attr[0] == 'src':
                    links.append(attr[1].strip())
        return links

    def get_logger(self, logfile):
        """
            初始化日志文件
        """
        logger = logging.getLogger(__name__)
        log_handler = logging.FileHandler(logfile)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log_handler.setFormatter(formatter)
        ll = (logging.CRITICAL,
              logging.ERROR,
              logging.WARNING,
              logging.INFO,
              logging.DEBUG)
        logger.setLevel(ll[4])
        log_handler.setLevel(ll[4])
        logger.addHandler(log_handler)
        return logger

    def start(self):
        print 'start at %s' % time.strftime('%Y-%m-%d %H:%M:%S')
        self.logger.info('task start from %s with depth %s' %
                         (self.url, self.depth))
        print   'task start from %s with depth %d'%(self.url, self.depth)
        print   'task will create %d thread(s)'%self.threads
        print   'task will stop when get %d resources'%self.maxsize
        print   'please wait for me to compete the task...'
        self.tasks_queue.put((self.url, self.depth))
        self.count+=1
        try:
            while True:
                try:
                    url, depth = self.tasks_queue.get(True, 1)# 阻塞１秒
                except Empty, e:  
                    if self.pool.undone_tasks():# 有任务尚未完成
                        continue
                    else:   
                        break# 跳出进行最后处理
                if not url in self.progress_urls:# 避免重复记录url
                    if self.count<=self.maxsize:
                        self.pool.spawn(self.crawl_page, *(url, depth))
                        self.progress_urls.append(url)
                        self.count+=1
                        self.resource_log.write(url+'\n')#向日志文件写入资源链接
                    else:
                        break
        except Exception, e:
            self.logger.critical('%s %s' % (e.__class__.__name__, e))
        finally:
            self.pool.joinall()#排空队列里的任务，安全的结束线程
            self.resource_log.close()#关闭文件描述符
            print 'task done!'
            print 'stop at %s' % time.strftime('%Y-%m-%d %H:%M:%S')
            self.logger.info('task done!')
 
def main():  
    usage = "usage: %prog [options] arg..."  
    parser = OptionParser(usage)  
    parser.add_option("-d", "--destination", dest="destination", default="http://www.hao123.com" , help="The destination spider will go")  
    parser.add_option("-m", "--maxsize", type="int",dest="maxsize", default=1000, help="Resource's maxsize of spider get,default 1000") 
    parser.add_option("-t", "--thread", type="int",dest="thread", default=4, help='parallel thread to grab data,default 4') 
    parser.add_option("-p", "--depth", type="int",dest="depth", default=3, help='depth in [1, 3) for spider,default 3')
    (options, args) = parser.parse_args()
    if len(args) != 0:
        parser.print_help()
        return
    spider = Spider(url=options.destination,
                    depth=options.depth,
                    threads=options.thread,
                    maxsize=options.maxsize)
    spider.start()
    
    
if __name__ == "__main__":
    main()  
    
