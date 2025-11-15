from colorama import Fore, init
import os

init()

def clear_screen():
    os.system("cls || clear")

def context_header(header: str) -> None:
    print(f"{Fore.WHITE}╭───( {Fore.CYAN}{header} {Fore.WHITE}){Fore.RESET}")

def context_key_value_point(key: str, value: str | int) -> None:
    print(f"{Fore.WHITE}│ - {Fore.BLUE}{key:<8} {Fore.WHITE}: {Fore.MAGENTA}{value}{Fore.RESET}")

def context_separator() -> None:
    print(f"{Fore.WHITE}│{Fore.RESET}")

def context_test_step_result(n_step: int, total_steps: int, name: str, result: bool, time: float) -> None:
    result_text = f"{Fore.GREEN}✅ passed" if result else f"{Fore.RED}❌ failed"
    time_text = f"{Fore.LIGHTBLACK_EX}({round(time, 2)}s)"
    print(f"{Fore.WHITE}├ {n_step}{Fore.LIGHTBLACK_EX}/{total_steps} {Fore.WHITE}{name} {Fore.LIGHTBLACK_EX}- {result_text} {time_text}{Fore.RESET}")
    
def context_finish(time_info: float = None) -> None:
    content = f"{Fore.WHITE}╰───•{Fore.RESET} "
    if time_info is not None:
        content += f"{Fore.LIGHTBLACK_EX}({round(time_info, 2)}s){Fore.RESET}"
    content += "\n"
    print(content)

def context_message_success(message: str) -> None:
    print(f"{Fore.WHITE}│ {Fore.GREEN}{message}{Fore.RESET}")

def context_message_error(message: str) -> None:
    print(f"{Fore.WHITE}│ {Fore.RED}{message}{Fore.RESET}")

def context_message_info(message: str) -> None:
    print(f"{Fore.WHITE}│ {Fore.WHITE}{message}{Fore.RESET}")


def print_config(config: dict[str, str | int]) -> None:
    context_header("⚙️ Tests configuration")
    for cfg_name, cfg_value in config.items():
        context_key_value_point(cfg_name, cfg_value)
    context_finish()
