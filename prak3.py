import sys
import json

# Коды команд согласно спецификации УВМ
CMD_LOAD = 0    # Загрузка константы в регистр
CMD_READ = 2    # Чтение из памяти в регистр
CMD_WRITE = 6   # Запись регистра в память со смещением
CMD_SQRT = 7    # Квадратный корень (будет на этапе 3)

def assemble(source_file, output_file, test_mode=False):
    """
    Ассемблер: преобразует текстовую программу в промежуточное представление
    """
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Ошибка: файл {source_file} не найден")
        return False

    program = []
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        parts = line.split()
        cmd_name = parts[0].upper()
        
        try:
            if cmd_name == "LOAD":
                # LOAD константа регистр_назначения
                const = int(parts[1])
                reg_dst = int(parts[2])
                if not (0 <= reg_dst < 256):
                    raise ValueError("Номер регистра должен быть от 0 до 255")
                program.append((CMD_LOAD, const, reg_dst))
                
            elif cmd_name == "READ":
                # READ регистр_источник регистр_назначения
                reg_src = int(parts[1])
                reg_dst = int(parts[2])
                if not (0 <= reg_src < 256 and 0 <= reg_dst < 256):
                    raise ValueError("Номер регистра должен быть от 0 до 255")
                program.append((CMD_READ, reg_src, reg_dst))
                
            elif cmd_name == "WRITE":
                # WRITE регистр_источник смещение регистр_адреса
                reg_src = int(parts[1])
                offset = int(parts[2])
                reg_addr = int(parts[3])
                if not (0 <= reg_src < 256 and 0 <= reg_addr < 256):
                    raise ValueError("Номер регистра должен быть от 0 до 255")
                program.append((CMD_WRITE, reg_src, offset, reg_addr))
                
            elif cmd_name == "SQRT":
                # SQRT адрес_источник адрес_назначения
                addr_src = int(parts[1])
                addr_dst = int(parts[2])
                program.append((CMD_SQRT, addr_src, addr_dst))
                
            else:
                print(f"Ошибка в строке {line_num}: неизвестная команда '{cmd_name}'")
                return False
                
        except (IndexError, ValueError) as e:
            print(f"Ошибка в строке {line_num}: {e}")
            return False
    
    # Режим тестирования
    if test_mode:
        print("Промежуточное представление программы:")
        print("=" * 50)
        for i, (opcode, *args) in enumerate(program):
            print(f"{i:3d}: {opcode} {args}")
        print("=" * 50)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(program, f, indent=2)
        print(f"Программа успешно ассемблирована в {output_file}")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении: {e}")
        return False

def test_assembler():
    """Тестирование ассемблера на примерах из спецификации"""
    print("Тестирование ассемблера...")
    
    test_program = """# Тестовая программа для Варианта 21
# Загрузка константы 25 в регистр 24
LOAD 25 24

# Чтение из памяти по адресу из регистра 34 в регистр 84
READ 34 84

# Запись регистра 52 в память по адресу регистра 122 + 5
WRITE 52 5 122

# Вычисление SQRT из ячейки 959 в ячейку 396
SQRT 959 396
"""
    
    with open('test.asm', 'w', encoding='utf-8') as f:
        f.write(test_program)
    
    success = assemble('test.asm', 'test_program.json', test_mode=True)
    return success

def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python prak3.py assemble <входной_файл> <выходной_файл> [test]")
        print("  python prak3.py test")
        return
    
    command = sys.argv[1]
    
    if command == "assemble":
        if len(sys.argv) < 4:
            print("Использование: python prak3.py assemble <вход> <выход> [test]")
            return
        source = sys.argv[2]
        output = sys.argv[3]
        test_mode = len(sys.argv) > 4 and sys.argv[4].lower() == "test"
        assemble(source, output, test_mode)
        
    elif command == "test":
        test_assembler()
        
    else:
        print(f"Неизвестная команда: {command}")

if __name__ == "__main__":
    main()