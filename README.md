# 🛸 ufo-vm
Это средство виртуализации, предоставляющее компилятор и виртуальную машину для исполнения. 
Компилятор воспринимает собственный intel подобный ассемблер с ограниченным набором инструкций. 
В текущей реализации поддерживается 16 инструкций с различными типами операндов и данных.

## ✏ Синтаксис
В листинге программы можно проинизиализировать сегменты кода и данных. При начале описания сегмента, 
следует использовать директивы `.code` или `.data` соответсвенно. После встречи с одной из директив, 
компилятор переходит в соответствующий режим анализа сегмента. Таким образом, сегмент данных не может содержать код, 
а сегмент кода - данные. Компилятор не чувствителен к отступам, разработчик волен расставлять их по своему усмотрению.
  
В исходном коде разрешены пустые строчки, а также предусмотрена возожность комментирования кода 
с помощью символа `#`. Все, что написано справа от `#`, считается комментарием и никак не обрабатывается компилятором.

### Сегмент .data
В общем случае, каждая отдельная строка в сегменте данных должна иметь следующий вид:  
`[метка] <тип> [инициализатор]`  

Ассемблер предусматривает работу исключительно с целочисленными типами данных:
| Тип |  Имя  |  Размер в байтах | 
|-----|-------|------------------|
|  db | byte  | 1                |
|  dh | short | 2                |
|  dw | dwort | 4                |
|  dq | qword | 8                |
  
Можно было заметить, что имя метки и инициализация совсем не обязательны при объявлении буфера памяти, cамое главное - 
указать тип. По умолчанию не инициализированные поля зануляются. 

Метки необходимы для дальнейшей адресации ячеек памяти в сегменте кода.
  
Следующий листинг считается правильным с точки зрения объявления сегмента данных:
```
.data
  banner    db    "Hello world!"
  binData   db    file(data.bin)
  byte_2    db    -100
  byte_3    db    0xff

  buff32    dq
            dq
            dq
            dq
```
  
Ассемблер позволяет использовать строки и содержимое файлов в качетсве инициализаторов памяти. В таком случае, 
размер выделяемой памяти будет зависить напрямую от размера инициализатора, а не от используемого спецификатора размера данных.
Однако, в выше описанных случаях хорошим тоном считается использование `db` в качетсве типа данных.  
  
Строки, как и бинарное содержимое файлов, будут распологаться в пямяти в нуль-терминированном виде.

### Сегмент .code
В общем случае, каждая отдельная строка в сегменте кода должна иметь следующий вид:  
`<инструкция> [операнды...]`
  
#### Полный набор инструкций с кратким описанием:
| Интрукция | Краткое описание                                  | Операнд 1     | Операнд 2     | Типы данных  |
|-----------|---------------------------------------------------|---------------|---------------|--------------|
| **exit**  | Выход из программы                                |               |               | db dh dw dq  |
| **mov**   | Перенос значения из op2 в op1                     | MEM           | LIT           | db dh dw dq  |
|           |                                                   | MEM           | MEM           |              |
|           |                                                   | MEM           | PTR           |              |
|           |                                                   | PTR           | MEM           |              |
| **add**   | Сумма операндов                                   | MEM           | LIT           | db dh dw dq  |
|           |                                                   | MEM           | MEM           |              |
|           |                                                   | MEM           | PTR           |              |
| **sub**   | Разность операндов                                | MEM           | LIT           | db dh dw dq  |
|           |                                                   | MEM           | MEM           |              |
|           |                                                   | MEM           | PTR           |              |
| **mul**   | Умножение операндов                               | MEM           | LIT           | db dh dw dq  |
|           |                                                   | MEM           | MEM           |              |
|           |                                                   | MEM           | PTR           |              |
| **div**   | Деление op1 на op2                                | MEM           | LIT           | db dh dw dq  |
|           |                                                   | MEM           | MEM           |              |
|           |                                                   | MEM           | PTR           |              |
| **xor**   | Логическое побитовое исключение                   | MEM           | LIT           | db dh dw dq  |
|           |                                                   | MEM           | MEM           |              |
|           |                                                   | MEM           | PTR           |              |
| **and**   | Логическое И                                      | MEM           | LIT           | db dh dw dq  |
|           |                                                   | MEM           | MEM           |              |
|           |                                                   | MEM           | PTR           |              |
| **or**    | Логическое ИЛИ                                    | MEM           | LIT           | db dh dw dq  |
|           |                                                   | MEM           | MEM           |              |
|           |                                                   | MEM           | PTR           |              |
| **rand**  | Случайное число в диапазоне [0, op2]              | MEM           | LIT           | db dh        |
|           |                                                   | MEM           | MEM           |              |
|           |                                                   | MEM           | PTR           |              |
| **ror**   | Циклический сдвиг на op2 вправо                   | MEM           | LIT           | db dh dw dq  |
|           |                                                   | MEM           | MEM           |              |
|           |                                                   | MEM           | PTR           |              |
| **rol**   | Циклический сдвиг на op2 влево                    | MEM           | LIT           | db dh dw dq  |
|           |                                                   | MEM           | MEM           |              |
|           |                                                   | MEM           | PTR           |              |
| **lea**   | Получить адрес op2                                | MEM           | MEM           | dh           |
| **jmp**   | Перенос выполнения на адрес op1, если op2 не ноль | CMEM          | LIT           | db dh dw dq  |
|           |                                                   | CMEM          | MEM           |              |
|           |                                                   | CMEM          | PTR           |              |
|           |                                                   | CPTR          | MEM           |              |
| **put**   | Вывести op1 в консоль                             | LIT           |               | db           |
|           |                                                   | MEM           |               |              |
|           |                                                   | PTR           |               |              |
| **get**   | Получить символ из буфера ввода                   | MEM           |               | db           |
|           |                                                   | PTR           |               |              |

Если выполнение операции несёт какой-любо результат, он всегда заносится в первый операнд.  
  
Как видно в таблице, каждая инструкция умеет работаь с различными типами операндов:
* LIT - литерал, задаваемый в исходном коде
* MEM - метка сегмента данных (по сути макрос, вместо которого подставляется адрес)
* PTR - метка на указатель сегмента данных (указывает на место в памяти, хранящее конечный адрес) 
* CMEM - метка сегмента кода
* CPTR - метка в сегменте данных, указывающая на место в сегменте кода

Рассмотрим листинг для примера:  
```
.data
    ptr  dh
    a    dw   
    b    dw   

.code
ptr:
    movw  a, 291     # MEM, LIT
    leah  ptr, a     # MEM, MEM
    movw  b, [ptr]   # MEM, PTR
    movw  [ptr], a   # PTR, MEM

    jmpb ptr, 1
```
  
Можно заметить, что каждая инструкция имеет постфикс, явно указывающий тип данных, с которым работает интсрукция.
Исходя из этого, инструкция `movw  a, 291` помещает по адресу `a` число `291`, закодированное в четыре байта с порядком
little-endian (в памяти будет иметь вид `0x23 0x01 0x00 0x00`).  

Слеудет обратить внимание на тип данных, с которым работает инструкция `lea`. Дело в том, что все адреса имеют размерность в
два байта, будь то сегмент кода или данных. 

> В контексте виртуальной машины, все адреса являются смещениями относительно начала сегмента

Имена меток должны быть уникальны для каждого из сегментов, то есть допускается повторное использование имени в другом сегменте (в примере `ptr` используется повторно).
Причина кроектся в том, что использование меток кода и данных не пересекается. Метки кода используются исключительно в качестве первого операнда инструкции `jmp`, для указания
места прыжка.

Компилятор предоставляет примитивную относительную адресную арифметику, например, инструкция
```
    movw  ptr+2, 100
```
положила бы значение `100` по адресу метки `a`  
  
Квадратные скобочки, окружающие операнд, обозначают, что он является поинтером, то есть операнд хранит в себе адрес, к которому инструкция должна обращаться.
```
    movw  b, [ptr]
```
то есть, данная инструкция переместит значение не из `ptr`, а из адреса, который лежит в `ptr`.  
  
### Регистры
Компилятор предоставляет десять восьмибайтных "регистров" для временного хранения данных. В виртуальной машине регистр, по сути, всего лишь буффер памяти с 
преопределенным именем.  

Регистры:
* rip
* r1-10

`rip` же отличает от остальных то, что он хранит адрес текущей исполняемой интрукции. Таким образом, в программе появляется возможность реилизовывать функции.
  
### Точка входа
Точкой входа считается метка `start` в сегменте кода. При её отсутсвии, точкой входа считается первая инструкция.

## ⚙ Компиляция
### Метки
В параграфе о синтаксисе можно найти информация про анализ меток.

### Трансляция
Опкод каждой интрукции умещается в один байт, остальные байты в интрукции хранят ее операнды. Размер и количество операндов зависит от операции, типа операндов и
тип данных.  
  
Опкод имеет следующую структуру:  
`код операции (4 бита) + тип операндов (2 бита) + тип данных (2 бита)`

Для примера, байткод инструкции  
`mov  r1, -1`  
будет выглядеть, как  
`13 08 00 ff ff ff ff ff ff ff ff`

Опкод `0x13` или `0b[0001][00][11]`. Отсюда получаем следующую информацию:
* это `mov`, так как она лежит под первым индексом в массиве обработчиков инструкций
* нулевые биты типа операндов гласят, что это адрес и литерал
* `0b11` определяет в качетсве типа данных QWORD, то есть конечные значения представляют из себя восьмибайтные знаковые числа.
  
Первый операнд адрес, значит это следующие после опкода два байта: `08 00`  
Декодируем как little-endian short и получаем `8`  
  
Но почему именно это значение? Напоинаю, все метки представляют из себя макросы, заменяемый на адреса, а адреса в свою очередь являются смещением от начала сегмента.
Все регистры лежит в самом начале сегмента данных, а `r1` лежит со смещением в восемь байтов от начала сегмента.  

Второй операнд кодирует литерал - восьмибайтное знаковое число - который следует поместить по адресу, находящемся в первом операнде.
Все отрицательные числа кодируются в обратном коде. 

### Структура скомпилированного файла
В самом начале скомпилированного файла находится 16-ти байтая (с учетом выравнивания) структура  
  
![изображение](https://github.com/lockheeed/ufo-vm/assets/47332822/3faaefee-c8f1-4dd9-9a97-ea9ff402719a)  
  
Сразу за заголовком последовательно располагаются сегмент кода и сегмент данных.
  
## 📃 Примеры кода
В директории `test-programs` представлены две программы, демонстрирующие все описанные выше возможности виртуальной машины и ассемблера.  
