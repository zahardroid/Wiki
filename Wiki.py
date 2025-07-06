import wikipediaapi
import re
from collections import deque

class WikipediaConsole:
    def __init__(self, lang='ru'):
        # Указываем user_agent как позиционный аргумент
        self.wiki = wikipediaapi.Wikipedia(
            'MyWikipediaBot/1.0 (myemail@example.com)',  # user_agent
            language=lang,
            extract_format=wikipediaapi.ExtractFormat.WIKI
        )
        self.current_page = None
        self.history = deque(maxlen=10)
        self.link_page = 0
        self.link_step = 10

    def clear_text(self, text):
        """Очистка текста от wiki-разметки"""
        return re.sub(r'\{\{.*?\}\}', '', text, flags=re.DOTALL)

    def get_sections(self, page):
        """Получение структурированного содержимого страницы"""
        if not page.exists():
            return []

        sections = []
        for section in page.sections:
            content = self.clear_text(section.text)
            if content.strip():
                sections.append({
                    'title': section.title,
                    'content': content,
                    'level': section.level
                })
        return sections

    def display_paragraphs(self, sections):
        """Интерактивный просмотр разделов статьи"""
        if not sections:
            print("В статье нет текстового содержимого.")
            return

        index = 0
        total = len(sections)

        while True:
            section = sections[index]
            print(f"\n\033[1m{section['title']}\033[0m" if section['title'] else "")
            print(section['content'])
            print(f"\nРаздел {index + 1}/{total} | Уровень: {section['level']}")

            cmd = input("\nКоманды: [N]ext, [P]rev, [G]oto, [S]earch, [M]enu: ").strip().lower()

            if cmd == 'm':
                break
            elif cmd == 'n' and index < total - 1:
                index += 1
            elif cmd == 'p' and index > 0:
                index -= 1
            elif cmd == 'g':
                try:
                    new_index = int(input(f"Введите номер раздела (1-{total}): ")) - 1
                    if 0 <= new_index < total:
                        index = new_index
                except ValueError:
                    print("Некорректный ввод")
            elif cmd == 's':
                query = input("Поиск по разделу: ").strip()
                if query:
                    found = False
                    for i, s in enumerate(sections[index:], index):
                        if query.lower() in s['content'].lower():
                            index = i
                            found = True
                            break
                    if not found:
                        print("Текст не найден")
            else:
                print("Некорректная команда")

    def show_links(self, page):
        """Отображение связанных страниц с пагинацией"""
        links = list(page.links.keys())
        total_links = len(links)

        if not links:
            print("Связанные страницы не найдены")
            return None

        start = self.link_page * self.link_step
        end = min(start + self.link_step, total_links)

        print(f"\nСвязанные страницы ({start + 1}-{end} из {total_links}):")
        for i, title in enumerate(links[start:end], start + 1):
            print(f"{i}. {title}")

        print("\nКоманды: [номер] Выбрать, [N]ext, [P]rev, [M]enu")
        return links

    def search(self):
        """Поиск статей по запросу"""
        query = input("\nВведите поисковый запрос: ").strip()
        if not query:
            return None

        results = self.wiki.page(query)
        if results.exists():
            return results

        search_results = self.wiki.search(query)
        if not search_results:
            print("Ничего не найдено")
            return None

        print("\nРезультаты поиска:")
        for i, title in enumerate(search_results, 1):
            print(f"{i}. {title}")

        try:
            choice = int(input("Выберите номер статьи (0 для отмены): "))
            if 1 <= choice <= len(search_results):
                return self.wiki.page(search_results[choice - 1])
        except ValueError:
            pass

        return None

    def run(self):
        """Основной цикл программы"""
        print("===== Консольный Вики-поисковик =====")

        # Первоначальный поиск
        while not self.current_page:
            self.current_page = self.search()

        # Основной цикл навигации
        while True:
            print(f"\n\033[1mТекущая статья:\033[0m {self.current_page.fullurl}")
            print(f"\033[1mЗаголовок:\033[0m {self.current_page.title}")

            sections = self.get_sections(self.current_page)
            links = list(self.current_page.links.keys())

            print("\nДоступные действия:")
            print("1. Просмотр статьи")
            print("2. Связанные страницы")
            print("3. Новый поиск")
            print("4. История просмотра")
            print("5. Выход")

            try:
                choice = int(input("Выберите действие (1-5): "))
            except ValueError:
                print("Некорректный ввод")
                continue

            if choice == 1:
                if sections:
                    self.display_paragraphs(sections)
                else:
                    print("Статья не содержит текстового содержимого")
            elif choice == 2:
                self.link_page = 0
                links_list = self.show_links(self.current_page)

                while links_list:
                    cmd = input("> ").strip().lower()

                    if cmd == 'm':
                        break
                    elif cmd == 'n':
                        self.link_page += 1
                        links_list = self.show_links(self.current_page)
                    elif cmd == 'p' and self.link_page > 0:
                        self.link_page -= 1
                        links_list = self.show_links(self.current_page)
                    else:
                        try:
                            num = int(cmd)
                            total_links = len(links_list)
                            start = self.link_page * self.link_step

                            if 1 <= num <= self.link_step and (start + num - 1) < total_links:
                                self.history.append(self.current_page)
                                new_page = self.wiki.page(links_list[start + num - 1])
                                if new_page.exists():
                                    self.current_page = new_page
                                    break
                                else:
                                    print("Страница недоступна")
                            else:
                                print("Некорректный номер")
                        except ValueError:
                            print("Некорректная команда")
            elif choice == 3:
                new_page = self.search()
                if new_page:
                    self.history.append(self.current_page)
                    self.current_page = new_page
            elif choice == 4:
                if self.history:
                    print("\nИстория просмотра:")
                    for i, page in enumerate(reversed(self.history), 1):
                        print(f"{i}. {page.title}")

                    try:
                        num = int(input("Введите номер для перехода (0 для отмены): "))
                        if 1 <= num <= len(self.history):
                            self.current_page = list(self.history)[-num]
                    except ValueError:
                        pass
                else:
                    print("История пуста")
            elif choice == 5:
                print("Работа программы завершена")
                break
            else:
                print("Некорректный выбор")


if __name__ == "__main__":
    wiki_search = WikipediaConsole()
    wiki_search.run()