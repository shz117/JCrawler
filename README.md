JCrawler
----------------------------
Yet another super basic web crawler. For course: Web Search Engines

Work flow:

1. accept input key words and number of result pages intended to be crawled

2. ask Google for top 10 websites for these key words as seed sites

3. do BFS starting from this 10 sites, dealing with some cases(Robots.txt, relative URL, etc.) along the way, print beautiful logs into terminal as well as LOGFILE

4. write pages into file after fully processed, to minimize disk IO

Feature:

1. using configurable multiple threads for downloading, more efficient

2. auto adjust parsing thread speed when number of fetched URLs "overshoots" desired number of sites

3. record level (distance between page and one of the original 10 pages) for further process


Todo:

1. downloading is bottleneck: try implementing pre-DNS resolvation feature to help

2. try non-blocking paradigm

3. implement priority for URLs in queues
