# generate baseline file for PHPStan analysis
vendor/bin/phpstan analyse --memory-limit=2G --generate-baseline=phpstan-baseline.neon

# grep for unknown class errors in the PHPStan error log and display the first 50 occurrences
grep -F "unknown class yii\\" phpstan-errors.txt | head -50

# grep for the "message" field in the phpstan-error.json file and display the results
grep -o '"message"[^,]*' phpstan-error.json

# find all phpstan.neon and phpstan.neon.dist files in the current directory and its subdirectories
find . -name 'phpstan*.neon' -o -name 'phpstan*.neon.dist'

# search for the string 'Genutils' in all PHP files within the src/www/wss2 directory and its subdirectories
grep -R "'Genutils'" src/www/wss2 --include="*.php"

# Clear PHPStan result cache
vendor/bin/phpstan clear-result-cache
# or 
rm -rf var/phpstan/cache && vendor/bin/phpstan analyse --memory-limit=1G

# Run PHPStan analysis on the AustraliaPostApi.php file with level 6 and memory limit of 1G, outputting errors to logs/phpstan-errors.txt
./vendor/bin/phpstan analyse src/www/wss2/console/controllers/StoresController.php -l 6 --memory-limit=1G --error-format=raw > logs/phpstan-errors.txt 2>&1

# Search for Nette\DI\ServiceCreationException in the project excluding certain directories
grep -R 'Codeception\TestCase\Test' . --exclude-dir=.git --exclude-dir=node_modules  --exclude-dir=vendor

# check php run command for class existence
php -r "require 'src/www/wss2/vendor/autoload.php'; var_dump(class_exists('Codeception\\TestCase\\Test'));"

# find which test file is referencing Codeception\TestCase\Test
grep -Rni "Codeception\\\\TestCase\\\\Test" src/www/wss2 --include="*.php"