downloads/retrieved:
	@mkdir $@

interim:
	@mkdir $@

downloads/retrieved/Reference.zip: downloads/retrieved
	curl -C - "http://www.comlab.uniroma3.it/retrieved/Reference.zip" --output $@

downloads/retrieved/ReTRiEVED-Reference: downloads/retrieved/Reference.zip
	unzip -jn $< -d $@

downloads/retrieved/PLR.zip: downloads/retrieved
	curl -C - "http://www.comlab.uniroma3.it/retrieved/PLR.zip" --output $@

downloads/retrieved/ReTRiEVED-PLR: downloads/retrieved/PLR.zip
	unzip -jn $< -d $@

downloads/retrieved/Jitter.zip: downloads/retrieved
	curl -C - "http://www.comlab.uniroma3.it/retrieved/Jitter.zip" --output $@

downloads/retrieved/ReTRiEVED-Jitter: downloads/retrieved/Jitter.zip
	unzip -jn $< -d $@

downloads/retrieved/Delay.zip: downloads/retrieved
	curl -C - "http://www.comlab.uniroma3.it/retrieved/Delay.zip" --output $@

downloads/retrieved/ReTRiEVED-Delay: downloads/retrieved/Delay.zip
	unzip -jn $< -d $@

downloads/retrieved/Throughput.zip : downloads/retrieved
	curl -C - "http://www.comlab.uniroma3.it/retrieved/Throughput.zip" --output $@

downloads/retrieved/ReTRiEVED-Throughput: downloads/retrieved/Throughput.zip
	unzip -jn $< -d $@

download: downloads/retrieved/ReTRiEVED-Reference
download: downloads/retrieved/ReTRiEVED-PLR
download: downloads/retrieved/ReTRiEVED-Jitter
download: downloads/retrieved/ReTRiEVED-Delay
download: downloads/retrieved/ReTRiEVED-Throughput

process: download
process: interim
	./parallel_process.sh $^ > ReTRiEVED-stdout.log 2>ReTriEVED-stderr.log

