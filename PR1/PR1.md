# Практическое занятие №1

## Задача 1

```bash
grep -o '^[^:]*' /etc/passwd | sort
```

## Задача 2

```bash
grep -v '^#' /etc/protocols | awk 'NF {print $2, $1}' | sort -rn | head -5
```

## Задача 3

```bash
#!/bin/bash

text="$1"
len=${#text}
border=$(printf '%*s' "$((len + 2))" '' | tr ' ' '-')

printf '+%s+\n| %s |\n+%s+\n' "$border" "$text" "$border"
```

## Задача 4

```bash
#!/bin/bash

grep -oE '[A-Za-z_][A-Za-z0-9_]*' "$1" | tr '[:upper:]' '[:lower:]' | sort -u | paste -sd' ' -
```

## Задача 5

```bash
#!/bin/bash

install -m 755 "$1" /usr/local/bin/
```

## Задача 6

```bash
#!/bin/bash

find "${1:-.}" -type f \( -name '*.c' -o -name '*.js' -o -name '*.py' \) | while IFS= read -r f; do
    first=$(head -n 1 "$f")
    case "$f" in
        *.c|*.js) pattern='^[[:space:]]*(//|/\*)' ;;
        *.py) pattern='^[[:space:]]*#' ;;
    esac
    if [[ $first =~ $pattern ]]; then
        echo "$f: есть"
    else
        echo "$f: нет"
    fi
done
```

## Задача 7

```bash
#!/bin/bash

find "${1:-.}" -type f -exec md5sum {} + | sort | uniq -w32 --all-repeated=separate
```

## Задача 8

```bash
#!/bin/bash

find "${2:-.}" -maxdepth 1 -type f -name "*.$1" -print0 | tar -cf archive.tar --null -T -
```

## Задача 9

```bash
#!/bin/bash

sed 's/    /\t/g' "$1" > "$2"
```

## Задача 10

```bash
#!/bin/bash

find "$1" -type f -name '*.txt' -empty
```