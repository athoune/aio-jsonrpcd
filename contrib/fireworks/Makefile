
bundle: node_modules/fireworks-js
	mkdir -p www-data/js
	./node_modules/.bin/esbuild	--bundle --minify --sourcemap src/fireworks.js > www-data/js/fireworks.js

node_modules/fireworks-js:
	yarn add fireworks-js
