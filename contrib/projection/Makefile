
bundle: node_modules/clappr www-data/js
	# --minify 
	./node_modules/.bin/esbuild	--bundle --sourcemap --outfile=www-data/js/projection.js src/projection.js

www-data/js:
	mkdir -p www-data/js

node_modules/clappr:
	yarn

serve:
	poetry run ./server.py

clean:
	rm -rf node_modules
