echo starting News host
python3 news_host.py 50100 50500 &
sleep 1s

echo starting News Provider/Publisher
python3 daily_news_provider.py 50414 50500 &
sleep 1s

echo starting News subscribers                                                   
python3 daily_news_subscriber.py 50421 50414 &                                   
python3 daily_news_subscriber.py 50422 50414 &

echo starting News Reporter Automation Test
python3 reporter_test_automation.py 50100

echo waiting 5 seconds to drain sent queue
sleep 5s

echo killing processes and exiting
kill %1
kill %2
kill %3
kill %4
