# librux
Skrypt pobiera oceny i wiadomości z dziennika szkolnego LIBRUS i wysyła je na maila.

Aby skrypt działał poprawnie wymagane są:
- przeglądarka chrome
- chromedriver (http://chromedriver.chromium.org/downloads)
- selenium (https://selenium-python.readthedocs.io)

Dodatkowo należy skonfigurować w pliku `cfg.yaml` konta Librusa dla wszystkich dzieci oraz konto SMTP do wysyłania maili o ocenach i wiadomościach w Librusie. 

## Instalacja zależności
```pip install -r requirements.txt```

## Konfiguracja Librusa
```
Ustawienia ->
Dane konta użytkownika ->
Używaj nowego systemu wiadomości -> NIE
```
