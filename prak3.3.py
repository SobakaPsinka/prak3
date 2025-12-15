import sys
import json
import math
import xml.etree.ElementTree as ET

CMD_LOAD = 0    # Загрузка константы в регистр
CMD_READ = 2    # Чтение из памяти в регистр
CMD_WRITE = 6   # Запись регистра в память со смещением
CMD_SQRT = 7    # Квадратный корень

# ЭТАП 1
def assemble(source_file, output_file, test_mode=False):
    """Ассемблер: преобразует текстовую программу в промежуточное представление"""
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
                program.append([CMD_LOAD, const, reg_dst])
                
            elif cmd_name == "READ":
                # READ регистр_источник регистр_назначения
                reg_src = int(parts[1])
                reg_dst = int(parts[2])
                if not (0 <= reg_src < 256 and 0 <= reg_dst < 256):
                    raise ValueError("Номер регистра должен быть от 0 до 255")
                program.append([CMD_READ, reg_src, reg_dst])
                
            elif cmd_name == "WRITE":
                # WRITE регистр_источник смещение регистр_адреса
                reg_src = int(parts[1])
                offset = int(parts[2])
                reg_addr = int(parts[3])
                if not (0 <= reg_src < 256 and 0 <= reg_addr < 256):
                    raise ValueError("Номер регистра должен быть от 0 до 255")
                program.append([CMD_WRITE, reg_src, offset, reg_addr])
                
            elif cmd_name == "SQRT":  # ЭТАП 3
                # SQRT адрес_источник адрес_назначения
                addr_src = int(parts[1])
                addr_dst = int(parts[2])
                program.append([CMD_SQRT, addr_src, addr_dst])
                
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
        for i, cmd in enumerate(program):
            opcode = cmd[0]
            args = cmd[1:]
            if opcode == CMD_LOAD:
                print(f"{i:3d}: LOAD {args[0]} -> reg[{args[1]}]")
            elif opcode == CMD_READ:
                print(f"{i:3d}: READ reg[{args[0]}] -> reg[{args[1]}]")
            elif opcode == CMD_WRITE:
                print(f"{i:3d}: WRITE reg[{args[0]}] -> memory[reg[{args[2]}]+{args[1]}]")
            elif opcode == CMD_SQRT:
                print(f"{i:3d}: SQRT memory[{args[0]}] -> memory[{args[1]}]")
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
    
    def execute_sqrt(self, src_addr, dst_addr):
        """ЭТАП 3: Выполнение команды SQRT"""
        try:
            value = self.memory[src_addr]
            if value < 0:
                result = 0
            else:
                result = int(math.isqrt(value))
            
            self.memory[dst_addr] = result
            print(f"SQRT: memory[{src_addr}]={value} -> sqrt={result} -> memory[{dst_addr}]")
            return True
        except IndexError:
            print(f"Ошибка SQRT: адрес вне диапазона ({src_addr} или {dst_addr})")
            return False
        except Exception as e:
            print(f"Ошибка SQRT: {e}")
            return False
    
    def run(self):
        """Выполнение программы (включая ЭТАП 3)"""
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
                        
                elif opcode == CMD_SQRT:  # ЭТАП 3
                    addr_src, addr_dst = cmd[1], cmd[2]
                    if not self.execute_sqrt(addr_src, addr_dst):
                        return False
                    
                else:
                    print(f"Неизвестный код операции: {opcode}")
                    return False
                    
            except IndexError as e:
                print(f"Ошибка выполнения команды {self.pc}: {e}")
                return False
            
            self.pc += 1
            commands_executed += 1
        
        print(f"Выполнено {commands_executed} команд (включая SQRT)")
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
        print(f"Память (интересные ячейки):")
        interesting = [100, 150, 200, 201, 396, 400, 959]
        for addr in interesting:
            if addr < len(self.memory):
                print(f"  memory[{addr:3d}] = {self.memory[addr]}")

def test_assembler():
    """Тестирование ассемблера"""
    print("Тестирование ассемблера...")
    
    test_program = """# Тестовая программа для Варианта 21 (все этапы)
# Этап 1-2: Базовые операции
LOAD 25 0
LOAD 100 1
WRITE 0 0 1      # memory[100] = 25
WRITE 1 50 1     # memory[150] = 100

# Этап 3: Команда SQRT
SQRT 100 200      # sqrt(25) -> memory[200]
SQRT 150 201      # sqrt(100) -> memory[201]

# Тест из спецификации Варианта 21
LOAD 625 2
WRITE 2 959 0    # memory[959] = 625
SQRT 959 396     # sqrt(625) -> memory[396]
"""
    
    with open('test_all.asm', 'w', encoding='utf-8') as f:
        f.write(test_program)
    
    success = assemble('test_all.asm', 'test_all.json', test_mode=True)
    return success

def test_interpreter_with_sqrt():
    """Тестирование интерпретатора с SQRT (этап 3)"""
    print("\nТестирование интерпретатора с SQRT...")
    
    test_program = [
        [CMD_LOAD, 25, 0],        # reg0 = 25
        [CMD_LOAD, 100, 1],       # reg1 = 100
        [CMD_WRITE, 0, 0, 1],     # memory[100] = 25
        [CMD_WRITE, 1, 50, 1],    # memory[150] = 100
        [CMD_SQRT, 100, 200],     # sqrt(25) -> memory[200]
        [CMD_SQRT, 150, 201],     # sqrt(100) -> memory[201]
        [CMD_LOAD, 625, 2],       # reg2 = 625
        [CMD_WRITE, 2, 959, 0],   # memory[959] = 625
        [CMD_SQRT, 959, 396],     # sqrt(625) -> memory[396]
    ]
    
    with open('test_with_sqrt.json', 'w') as f:
        json.dump(test_program, f)
    
    vm = VirtualMachine()
    vm.load_program('test_with_sqrt.json')
    vm.run()
    
    print("\nПроверка результатов:")
    tests = [
        (100, 25, "Исходное значение"),
        (150, 100, "Исходное значение"),
        (200, 5, "sqrt(25)"),
        (201, 10, "sqrt(100)"),
        (959, 625, "Исходное значение для теста"),
        (396, 25, "sqrt(625) - тест из спецификации"),
    ]
    
    all_passed = True
    for addr, expected, description in tests:
        actual = vm.memory[addr]
        if actual == expected:
            print(f"✓ memory[{addr:3d}] = {actual:3d} - {description}")
        else:
            print(f"✗ memory[{addr:3d}] = {actual:3d} (ожидалось {expected:3d}) - {description}")
            all_passed = False
    
    vm.dump_memory_xml(0, 1000, 'memory_with_sqrt.xml')
    vm.print_state()
    
    return all_passed

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
        print("  Этап 2-3 (Интерпретатор): python prak3.py run <программа> <дамп> <начало> <конец>")
        print("  Тесты всех этапов: python prak3.py test")
        print("  Тест этапа 3 (SQRT): python prak3.py test-sqrt")
        print("\nПримеры:")
        print("  python prak3.py assemble program.asm program.json test")
        print("  python prak3.py run program.json dump.xml 0 1000")
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
        
    elif command == "run":
        if len(sys.argv) < 6:
            print("Использование: python prak3.py run <программа> <дамп> <начало> <конец>")
            print("Пример: python prak3.py run program.json dump.xml 0 1000")
            return
        program = sys.argv[2]
        dump = sys.argv[3]
        start = int(sys.argv[4])
        end = int(sys.argv[5])
        run_vm(program, dump, start, end)
        
    elif command == "test":
        print("Запуск всех тестов (этапы 1-3)...")
        test1 = test_assembler()
        test2 = test_interpreter_with_sqrt()
        
        if test1 and test2:
            print("\n Все этапы пройдены успешно!")
            print("   Этап 1: Ассемблер")
            print("   Этап 2: Интерпретатор (память)")
            print("   Этап 3: Команда SQRT")
        else:
            print("\n Некоторые тесты не пройдены!")
        
    elif command == "test-sqrt":
        print("Тестирование только этапа 3 (SQRT)...")
        
        # Быстрый тест SQRT
        vm = VirtualMachine()
        vm.memory[959] = 625
        vm.memory[100] = 25
        vm.memory[150] = 100
        
        print("Исходные данные:")
        print(f"  memory[959] = {vm.memory[959]}")
        print(f"  memory[100] = {vm.memory[100]}")
        print(f"  memory[150] = {vm.memory[150]}")
        
        print("\nВыполнение SQRT команд:")
        vm.execute_sqrt(959, 396)
        vm.execute_sqrt(100, 200)
        vm.execute_sqrt(150, 201)
        
        print("\nРезультаты:")
        print(f"  memory[396] = {vm.memory[396]} (должно быть 25)")
        print(f"  memory[200] = {vm.memory[200]} (должно быть 5)")
        print(f"  memory[201] = {vm.memory[201]} (должно быть 10)")
        
        if (vm.memory[396] == 25 and 
            vm.memory[200] == 5 and 
            vm.memory[201] == 10):
            print("\n Этап 3 (SQRT) пройден успешно!")
        else:
            print("\n Этап 3 (SQRT) не пройден!")
        
    else:
        print(f"Неизвестная команда: {command}")

if __name__ == "__main__":
    main()