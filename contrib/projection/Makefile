
bundle: bundle-js bundle-css

bundle-js: node_modules www-data/js
	# --minify 
	./node_modules/.bin/esbuild	--bundle --sourcemap --outfile=www-data/js/projection.js src/js/projection.js


www-data/js:
	mkdir -p www-data/js

clan-js:
	rm -rf www-data/js

node_modules:
	yarn

serve:
	poetry run ./server.py

css: | sass bundle-css

bundle-css:
	./node_modules/.bin/esbuild	--bundle --minify --sourcemap --outfile=www-data/css/index.css build/sass/index.css

src/sass/bulma: node_modules
	ln -s ../../node_modules/bulma src/sass/

build/sass:
	mkdir -p build/sass

sass: src/sass/bulma build/sass
	mkdir -p www-data/css
	./node_modules/.bin/sass src/sass/index.scss build/sass/index.css

clean-css:
	rm -rf www-data/css
	rm -rf build/sass

clean: clean-css
	rm -rf node_modules
	rm -rf build
