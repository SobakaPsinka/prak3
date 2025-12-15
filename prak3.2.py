import sys
import json
import xml.etree.ElementTree as ET

# Коды команд согласно спецификации УВМ
CMD_LOAD = 0    # Загрузка константы в регистр
CMD_READ = 2    # Чтение из памяти в регистр
CMD_WRITE = 6   # Запись регистра в память со смещением
CMD_SQRT = 7    # Квадратный корень (будет на этапе 3)

# ЭТАП 1
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

# ЭТАП 2
class VirtualMachine:
    """Виртуальная машина УВМ (Вариант 21)"""
    
    def __init__(self, mem_size=1024, num_regs=256):
        self.memory = [0] * mem_size
        self.regs = [0] * num_regs
        self.pc = 0  # Program counter
        self.program = []
        
    def load_program(self, program_file):
        """Загрузка программы из JSON файла"""
        try:
            with open(program_file, 'r', encoding='utf-8') as f:
                self.program = json.load(f)
            print(f"Загружена программа из {program_file} ({len(self.program)} команд)")
            return True
        except Exception as e:
            print(f"Ошибка загрузки программы: {e}")
            return False
    
    def run(self):
        """Выполнение программы"""
        self.pc = 0
        commands_executed = 0
        
        while self.pc < len(self.program):
            cmd = self.program[self.pc]
            opcode = cmd[0]
            
            try:
                if opcode == CMD_LOAD:
                    const, reg_dst = cmd[1], cmd[2]
                    self.regs[reg_dst] = const
                    
                elif opcode == CMD_READ:
                    reg_src, reg_dst = cmd[1], cmd[2]
                    addr = self.regs[reg_src]
                    self.regs[reg_dst] = self.memory[addr]
                    
                elif opcode == CMD_WRITE:
                    reg_src, offset, reg_addr = cmd[1], cmd[2], cmd[3]
                    addr = self.regs[reg_addr] + offset
                    if 0 <= addr < len(self.memory):
                        self.memory[addr] = self.regs[reg_src]
                    else:
                        print(f"Ошибка: адрес {addr} вне диапазона памяти")
                        return False
                        
                elif opcode == CMD_SQRT:
                    # заглушка
                    addr_src, addr_dst = cmd[1], cmd[2]
                    print(f"Команда SQRT будет реализована на этапе 3")
                    self.memory[addr_dst] = 0
                    
                else:
                    print(f"Неизвестный код операции: {opcode}")
                    return False
                    
            except IndexError as e:
                print(f"Ошибка выполнения команды {self.pc}: {e}")
                return False
            
            self.pc += 1
            commands_executed += 1
        
        print(f"Выполнено {commands_executed} команд")
        return True
    
    def dump_memory_xml(self, start_addr, end_addr, dump_file):
        """Сохранение дампа памяти в XML формате"""
        try:
            root = ET.Element("memory_dump")
            root.set("start", str(start_addr))
            root.set("end", str(end_addr))
            
            for addr in range(start_addr, min(end_addr + 1, len(self.memory))):
                cell = ET.SubElement(root, "cell")
                cell.set("address", str(addr))
                cell.set("value", str(self.memory[addr]))
            
            tree = ET.ElementTree(root)
            tree.write(dump_file, encoding="utf-8", xml_declaration=True)
            print(f"Дамп памяти сохранен в {dump_file}")
            return True
            
        except Exception as e:
            print(f"Ошибка при сохранении дампа: {e}")
            return False
    
    def print_state(self):
        """Вывод состояния ВМ"""
        print("\nСостояние виртуальной машины:")
        print(f"PC: {self.pc}")
        print(f"Регистры (первые 10): {self.regs[:10]}")
        print(f"Память (первые 20 ячеек): {self.memory[:20]}")

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

def test_interpreter():
    """Тестирование интерпретатора"""
    print("\nТестирование интерпретатора...")
    
    test_program = [
        [CMD_LOAD, 100, 0],
        [CMD_LOAD, 200, 1],
        [CMD_WRITE, 0, 0, 1],
        [CMD_READ, 1, 2],
    ]
    
    with open('test_prog.json', 'w') as f:
        json.dump(test_program, f)
    
    vm = VirtualMachine()
    vm.load_program('test_prog.json')
    vm.run()
    
    vm.dump_memory_xml(0, 50, 'memory_dump.xml')
    vm.print_state()
    
    if vm.memory[200] == 100 and vm.regs[2] == 100:
        print("Тест пройден успешно!")
        return True
    else:
        print("Тест не пройден!")
        return False

def run_vm(program_file, dump_file, start_addr, end_addr):
    """Запуск виртуальной машины"""
    vm = VirtualMachine()
    
    if not vm.load_program(program_file):
        return False
    
    if not vm.run():
        return False
    
    if not vm.dump_memory_xml(start_addr, end_addr, dump_file):
        return False
    
    vm.print_state()
    return True

def main():
    """Главная функция"""
    if len(sys.argv) < 2:
        print("Использование:")
        print("  Этап 1 (Ассемблер): python prak3.py assemble <вход> <выход> [test]")
        print("  Этап 2 (Интерпретатор): python prak3.py run <программа> <дамп> <начало> <конец>")
        print("  Тесты: python prak3.py test")
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
        
    elif command == "run":
        if len(sys.argv) < 6:
            print("Использование: python prak3.py run <программа> <дамп> <начало> <конец>")
            print("Пример: python prak3.py run program.json dump.xml 0 100")
            return
        program = sys.argv[2]
        dump = sys.argv[3]
        start = int(sys.argv[4])
        end = int(sys.argv[5])
        run_vm(program, dump, start, end)
        
    elif command == "test":
        print("Запуск тестов...")
        test1 = test_assembler()
        test2 = test_interpreter()
        if test1 and test2:
            print("\nВсе тесты пройдены успешно!")
        else:
            print("\nНекоторые тесты не пройдены!")
        
    else:
        print(f"Неизвестная команда: {command}")

if __name__ == "__main__":
    main()

# Входные данные
# python prak3.py assemble test_vm.asm test_vm.json test
# python prak3.py run test_vm.json dump.xml 0 250