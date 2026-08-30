vendor/bin/phpstan analyse --memory-limit=1G --error-format=raw > phpstan-errors.txt 2>&1

vendor/bin/phpstan analyse src/www/wss2/api/controllers/AppsettingsController.php --memory-limit=512G --error-format=json > phpstan-error.json

vendor/bin/phpstan analyse --memory-limit=1G --generate-baseline=phpstan-baseline.neon


grep -F "unknown class yii\\" phpstan-errors.txt | head -50
grep -o '"message"[^,]*' phpstan-error.json
find . -name 'phpstan*.neon' -o -name 'phpstan*.neon.dist'