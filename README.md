# hlk-ld2450-breath-detector-py

Визуализация перемещения человека в пространстве по данным радара HLK-LD2450 (ESP32).

## Архитектура (MVVM, PySide6)

```
COM (ESP32) ──► SerialWorker (поток) ──► parse_raw_line() ──► signal frameReady(RadarFrame)
                                                       │
   ┌───────────────────────────────────────────────────┼───────────────────────────┐
   ▼                                    ▼                                  ▼
ConnectionVM (статус)          HeatmapVM.ingest(frame)              InfoPanel.update_frame(frame)
                                  └► HeatmapModel (numpy)          (будущие вкладки/обработчики)
                                     └► signal updated(payload)
                                              │
                                              ▼
                                       HeatmapView (render ~30fps, независимо от данных)
```

Потоки не блокируются: чтение COM в `SerialWorker` (отдельный `QThread`),
математика буфера дёшевая, отрисовка matplotlib троттлится таймером.

## Где что лежит

- `core/frame.py` — чистые данные `Target`, `RadarFrame` (без Qt).
- `core/protocol.py` — `parse_raw_line(line) -> RadarFrame | None` (парсер протокола).
- `models/serial_source.py` — `SerialWorker`: чтение COM в потоке, шлёт `frameReady`/`rawReady`.
- `models/heatmap_model.py` — `HeatmapModel`: numpy-буферы, fade/trail, статистика (ядро обработки сигнала).
- `viewmodels/settings_vm.py` — настройки визуализации (fade, intensity, trail…).
- `viewmodels/connection_vm.py` — порт/baud/статус подключения.
- `viewmodels/heatmap_vm.py` — мостит `HeatmapModel` и View через сигнал `updated`.
- `views/connection_panel.py`, `settings_panel.py`, `info_panel.py` — левые панели.
- `views/heatmap_view.py` — matplotlib-canvas, рендер по таймеру.
- `views/main_window.py` — `QMainWindow` + `QTabWidget` (вкладки = новый функционал).
- `main.py` — сборка и связывание всех слоёв.

## Куда дописывать новый функционал

1. **Новая вкладка с графиком** (например, сырые сигналы, спектр, дыхание):
   - `views/xxx_view.py` (наследник `QWidget`) + при необходимости `viewmodels/xxx_vm.py`.
   - Подпишитесь на `worker.frameReady` (или на `heatmap_vm.updated`).
   - Зарегистрируйте вкладку в `main.py`: `window.add_tab(xxx_view, "Название")`.

2. **Новая логика обработки сигнала** (фильтры, детекция дыхания, трекинг):
   - метод/класс в `models/` (например `models/breath_detector.py`),
   - подпишитесь на `frameReady`, результат отдавайте во ViewModel -> View.

3. **Смена протокола / больше целей**: правьте `core/frame.py` и `core/protocol.py`.
   Остальные слои зависят только от `RadarFrame`.

## Запуск

Используется виртуальное окружение проекта `.venv` (PySide6 + matplotlib + numpy + pyserial).

```
.venv\Scripts\python.exe main.py
```
