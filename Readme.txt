测试环境：ubuntu 10.04 python 2.6.5
需要的第三方模块：BeautifulSoup

使用方法：
可以直接输入命令python T_Spider.py以默认参数运行
具体使用方法请输入命令python T_Spider.py -h查看

注意事项：
程序运行后会在当前目录创建一个Resource.txt文件，用于记录爬取到的资源链接，每次运行会将上一次的结果覆盖，程序未结束前打开Resource.txt有可能还没有写入
同时也会在当前目录创建一个sys_run.log的系统运行日志文件，下次的运行结果不会覆盖之前的，会以追加的方式写入
如果设置的爬取深度不够，即使没有达到资源上限爬虫也会结束
在windows下运行，没有换行，排版很乱
运行时间稍长，请耐心等待（本机测试，以默认参数运行时间为３５秒）

程序概述：
爬虫采用广度优先策略，以线程池的方式实现。
可以爬取a,img,link,script标签里的链接
TreadPoolSlot类是一个具体的线程实现，TreadPool类负责管理创建的线程，Spider类则是一个具体的爬虫。Spider.start方法向TreadPool中添加任务，而TreadPoolSlot不停的从TreadPool的任务队列中取出任务执行

TODO:
优化get_all_links方法（经测试发现在这个方法上花费的时间比较多）
增强爬虫的适应性。比如更改http头部的User-Agent域，伪装成浏览器发出的请求；控制并发数，以防被封ip
增加打开url的速度，设置头部的accept-encoding域为gzip
增加资源下载模块，将链接对应的资源下载到本地
改进程序的filter_links方法，使其不但可以爬取hao123下的资源，也可以爬取其他网站的资源
线程的结束应该更优雅


