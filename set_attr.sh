#!/bin/sh
# полный путь до скрипта
export ABSOLUTE_FILENAME=`readlink -e "$0"`
# каталог, в котором лежит скрипт
export DIRECTORY=`dirname "$ABSOLUTE_FILENAME"`
cd $DIRECTORY

(find . -name "*" -exec chmod go-rwx {} \;); (find . -name "*" -type d -exec chmod 700 {} \;); (find . -name "*.ico" -type f -exec chmod 400 {} \;); (find . -name "*.gif" -type f -exec chmod 400 {} \;); (find . -name "*.png" -type f -exec chmod 400 {} \;); (find . -name "*.sh" -type f -exec chmod 500 {} \;); (find . -name "*.bat" -type f -exec chmod 500 {} \;);
