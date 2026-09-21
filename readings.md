# Литература и материалы курса

## Как пользоваться этим списком

Список организован по десяти темам курса в том порядке, в каком они читаются. В каждой теме сначала кратко сформулировано, **что именно студент должен понять** (это одновременно и критерий на экзамене), затем идут работы с пометками:

- **[обязательно]** — читается до лекции; на семинаре обсуждается и предполагается известным. Обычно 1–3 работы на тему, суммарно 30–60 страниц.
- **[дополнительно]** — для проекта, для доклада на семинаре или для тех, кто хочет глубже.

Аудитория курса — магистры с полной математической базой (линейная алгебра, теория вероятностей, математический анализ), поэтому статьи читаются **в оригинале и целиком**, включая формулы и приложения. Пересказы на Habr и в блогах допустимы как вход, но не как замена источника. Инженерные посты компаний (Anthropic, OpenAI, Cognition, Manus) вынесены в отдельный раздел: это не научные статьи, но именно они формируют текущую практику, и на них построена значительная часть лабораторных.

Даты и версии указаны на сентябрь 2026 года. Спецификации и документация фреймворков устаревают быстрее статей: перед лекцией проверяйте актуальную версию.

---

## Учебники и обзоры

- Chip Huyen, *AI Engineering: Building Applications with Foundation Models* (O'Reilly, 2025) — https://github.com/chiphuyen/aie-book — основной учебник курса по инженерной части: оценка, RAG и агенты, оптимизация инференса, работа с данными. Главы про evaluation — лучшее системное изложение темы 8.
- Jay Alammar, Maarten Grootendorst, *Hands-On Large Language Models* (O'Reilly, 2024) — https://github.com/HandsOnLLM/Hands-On-Large-Language-Models — визуальное введение в токены, эмбеддинги, attention и генерацию; используется в темах 1–2 и 6 как быстрый вход перед статьями.
- Jay Alammar, Maarten Grootendorst, *An Illustrated Guide to AI Agents* (O'Reilly, сентябрь 2026) — https://www.oreilly.com/library/view/an-illustrated-guide/9798341662681/ — продолжение предыдущей книги: архитектура агента, память, reasoning-модели, многоагентные системы. Наиболее близкий к курсу по охвату учебник.
- Sebastian Raschka, *Build a Large Language Model (From Scratch)* (Manning, 2024) — https://github.com/rasbt/LLMs-from-scratch — для тех, кто хочет увидеть внутренности: собственная реализация токенизатора, attention, KV-cache и генерации. Рекомендуется как опора для лабораторной по темам 1–2.
- Antonio Gulli, *Agentic Design Patterns: A Hands-On Guide to Building Intelligent Systems* (Springer, 2025) — https://link.springer.com/book/10.1007/978-3-032-01402-3 — каталог из 21 паттерна (routing, reflection, planning, multi-agent, guardrails, memory и др.) с кодом на ADK/LangGraph/CrewAI. Справочник для темы 5 и для проектов.
- Nicole Koenigstein, *AI Agents: The Definitive Guide: Design, Deployment, and Evaluation* (O'Reilly, октябрь 2026) — https://www.oreilly.com/library/view/ai-agents-the/0642572247775/ — системный и продакшн-уровень: развёртывание, наблюдаемость, оценка. Дополнение к темам 8–9.
- Lilian Weng, «LLM Powered Autonomous Agents» (блог, июнь 2023) — https://lilianweng.github.io/posts/2023-06-23-agent/ — канонический обзор, задавший рамку «планирование + память + инструменты»; читается первым в теме 5, хорошо показывает, что изменилось за три года.
- Nathan Lambert, *RLHF Book* (открытая книга, 2025) — https://rlhfbook.com/ — единственный полноценный учебник по post-training: reward models, PPO, DPO, RLVR. Основа темы 10.

---

## 1. Токены и токенизация

**Что нужно понять.** Модель работает не над символами и не над словами, а над последовательностью целочисленных идентификаторов, которые порождает отдельно обученный субсловный токенизатор (BPE, SentencePiece/Unigram). Токенизатор — это схема сжатия, выученная на корпусе с преобладанием английского; поэтому число токенов на символ, а значит стоимость, задержка и «вместимость» контекстного окна, зависит от языка: кириллица обходится в 2–3 раза дороже английского, некоторые языки — до 15 раз. Числа, пробелы, отступы в коде и редкий Unicode токенизируются нерегулярно, и это конкретный источник ошибок в арифметике и посимвольных операциях. Тарификация идёт по токенам и асимметрична: выходные токены в 4–5 раз дороже входных, а закешированные входные токены стоят около 10% от обычной цены — именно это делает длинные агентные циклы экономически возможными. Считать токены надо токенизатором провайдера или его count-tokens API, а не по словам.

- [обязательно] Sennrich, Haddow, Birch, «Neural Machine Translation of Rare Words with Subword Units» (ACL 2016) — https://arxiv.org/abs/1508.07909 — алгоритм BPE как он есть; достаточно разделов 3 и 5.
- [обязательно] Andrej Karpathy, «Let's build the GPT Tokenizer» (видеолекция, февраль 2024) — https://www.youtube.com/watch?v=zduSFxRajkE — реализация BPE с нуля и разбор «странностей» токенизации; лабораторная 1 повторяет её на русско-английском корпусе.
- [обязательно] Petrov, La Malfa, Torr, Bibi, «Language Model Tokenizers Introduce Unfairness Between Languages» (NeurIPS 2023) — https://arxiv.org/abs/2305.15425 — количественная оценка «налога на язык»; взять методику измерения и таблицы по языкам.
- [дополнительно] Anthropic, «Token counting» — https://platform.claude.com/docs/en/build-with-claude/token-counting и «Prompt caching» — https://platform.claude.com/docs/en/build-with-claude/prompt-caching — как считать токены через API и какова реальная тарифная сетка с учётом кеша.
- [дополнительно] tiktoken — https://github.com/openai/tiktoken ; интерактивный Tiktokenizer — https://tiktokenizer.vercel.app/ — инструменты для лабораторной.

---

## 2. Инференс LLM: KV-cache, prefill/decode, prompt caching, sampling, constrained decoding

**Что нужно понять.** Генерация авторегрессионна: каждый выходной токен требует полного прямого прохода, обусловленного всеми предыдущими токенами, поэтому стоимость линейна по длине выхода, тогда как обработка промпта (prefill) — один параллельный проход. KV-cache хранит ключи и значения attention для уже обработанных токенов; поскольку он зависит только от префикса, одинаковые префиксы промптов можно переиспользовать между запросами — это и есть prefix/prompt caching, и отсюда инженерное правило: системный промпт и описания инструментов должны быть байтово стабильны и только дописываться. Задержка раскладывается на TTFT (определяется prefill, пропорционален длине входа) и время декодирования (токенов в секунду, ограничено пропускной способностью памяти); батчинг меняет пропускную способность на задержку. Параметры сэмплирования (temperature, top-p) переформируют распределение следующего токена; constrained decoding маскирует логиты автоматом по грамматике или JSON-схеме, так что модель физически не может выдать невалидную структуру — так реализованы structured outputs и надёжные аргументы tool calls.

- [обязательно] Kwon et al., «Efficient Memory Management for Large Language Model Serving with PagedAttention» (SOSP 2023) — https://arxiv.org/abs/2309.06180 — статья vLLM; взять модель памяти KV-cache и разделение prefill/decode.
- [обязательно] Pope et al., «Efficiently Scaling Transformer Inference» (MLSys 2023) — https://arxiv.org/abs/2211.05102 — анализ, почему decode упирается в память, а prefill — в вычисления; формулы для оценки TTFT и throughput.
- [обязательно] Manus, «Context Engineering for AI Agents: Lessons from Building Manus» (июль 2025) — https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus — KV-cache hit rate как ключевая продакшн-метрика агента; соотношение вход/выход 100:1.
- [дополнительно] Dong et al., «XGrammar: Flexible and Efficient Structured Generation Engine for LLMs» (2024) — https://arxiv.org/abs/2411.15100 — как реализуется грамматическое ограничение декодирования без потери скорости.
- [дополнительно] OpenAI, «Introducing Structured Outputs in the API» (2024) — https://openai.com/index/introducing-structured-outputs-in-the-api/ — продуктовое описание того же механизма.

---

## 3. Контекст и context engineering

**Что нужно понять.** Контекстное окно — вся рабочая память модели, и attention над ним — конечный бюджет: каждый токен конкурирует за внимание, и качество деградирует задолго до номинального предела. «Lost in the Middle» показал U-образную кривую: информация в начале и конце используется, в середине — игнорируется; отчёт Chroma «Context Rot» на 18 моделях показал монотонную деградацию с ростом длины входа даже на тривиальных задачах; Breunig описал четыре режима отказа контекста (poisoning, distraction, confusion, clash). Context engineering — дисциплина принятия решения, какие именно токены присутствуют на каждом шаге: системный промпт «на правильной высоте», подгрузка по запросу вместо предзагрузки, очистка результатов инструментов, компакция (суммаризация транскрипта при росте) и внешняя память (файлы, scratchpad) как иерархия памяти. Ключевое различие — между фиксированным промптом и динамически курируемым контекстом; субагенты нужно понимать в первую очередь как механизм изоляции контекста.

- [обязательно] Liu et al., «Lost in the Middle: How Language Models Use Long Contexts» (TACL 2024) — https://arxiv.org/abs/2307.03172 — методика needle-in-a-haystack и U-кривая; лабораторная 3 воспроизводит эксперимент.
- [обязательно] Chroma, «Context Rot: How Increasing Input Tokens Impacts LLM Performance» (технический отчёт, июль 2025) — https://research.trychroma.com/context-rot — деградация с ростом длины на 18 моделях; взять дизайн экспериментов.
- [обязательно] Anthropic, «Effective context engineering for AI agents» (сентябрь 2025) — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents — компакция, структурированные заметки, субагенты как изоляция контекста.
- [дополнительно] Drew Breunig, «How Long Contexts Fail» (июнь 2025) — https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html и «How to Fix Your Context» — https://www.dbreunig.com/2025/06/26/how-to-fix-your-context.html — таксономия отказов и приёмов; удобно для семинара.
- [дополнительно] Manus (см. тему 2) — append-only контекст, «оставлять ошибки в контексте», файловая система как контекст.

---

## 4. Tool calling, function calling, MCP

**Что нужно понять.** Вызов инструмента — не магия: модель дообучена выдавать блок, ограниченный специальными токенами, с именем функции и JSON-аргументами по схеме, которая была сериализована в промпт; harness парсит блок, исполняет функцию, добавляет результат сообщением роли tool, и цикл повторяется. Описания инструментов (имя, описание, схема параметров) — часть промпта: описание и есть интерфейс, и его формулировка измеримо меняет поведение. Параллельные вызовы — просто несколько блоков в одном ходе; решению «когда вызывать» модель обучается на синтетических и размеченных траекториях. Два приёма масштабирования: tool search / отложенная загрузка (не класть сотни схем в контекст, дать агенту находить инструменты по запросу) и code-execution-as-tool (модель пишет программу, которая композирует много вызовов API; CodeAct и «Code execution with MCP»), что сокращает токены на порядки и даёт циклы, фильтрацию и обработку ошибок бесплатно. MCP стандартизирует интерфейс между агентом и инструментами: tools, resources, prompts на стороне сервера, elicitation на стороне клиента, транспорты stdio и Streamable HTTP.

- [обязательно] Schick et al., «Toolformer: Language Models Can Teach Themselves to Use Tools» (2023) — https://arxiv.org/abs/2302.04761 — как модель обучается решать, когда и какой инструмент вызвать; самообучение через полезность вызова.
- [обязательно] Wang et al., «Executable Code Actions Elicit Better LLM Agents» (CodeAct, ICML 2024) — https://arxiv.org/abs/2402.01030 — код как действие вместо JSON; эмпирика по сокращению шагов.
- [обязательно] Anthropic, «Writing effective tools for AI agents — using AI agents» (сентябрь 2025) — https://www.anthropic.com/engineering/writing-tools-for-agents — пространство имён, экономные ответы инструментов, оценка инструментов агентами; основа A/B-эксперимента в лабораторной 4.
- [обязательно] Model Context Protocol, спецификация (ревизия 2026-07-28) — https://modelcontextprotocol.io/specification/latest — примитивы и транспорты; читать разделы про stateless core и Streamable HTTP.
- [дополнительно] Anthropic, «Code execution with MCP: building more efficient agents» (ноябрь 2025) — https://www.anthropic.com/engineering/code-execution-with-mcp и «Advanced tool use» (Tool Search Tool) — https://www.anthropic.com/engineering/advanced-tool-use — два приёма масштабирования.
- [дополнительно] Berkeley Function Calling Leaderboard (Patil et al.) — https://gorilla.cs.berkeley.edu/leaderboard.html — как оценивают качество tool calling; категории ошибок.

---

## 5. Архитектуры агентов и agent loop

**Что нужно понять.** Агент — это LLM в цикле со средой: наблюдение → рассуждение → действие → наблюдение; формально это политика в POMDP, где состояние среды наблюдается через результаты инструментов, а «состояние агента» — его контекст. ReAct сделал цикл явным, чередуя рассуждения и действия; Reflexion добавил вербальную самокритику, сохраняемую между попытками; Tree of Thoughts и LATS заменили линейный цикл поиском (BFS/MCTS по состояниям рассуждения или действия); Plan-and-Execute разделяет планировщик и исполнителей. Ключевое различие по Anthropic: workflows (поток управления задан кодом, LLM внутри — prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer) против agents (LLM сам определяет поток управления и вызовы инструментов); правило — использовать простейшее, что работает. Многоагентные системы лучше всего понимать как управление контекстом: система Anthropic для research параллелит поиск в ширину, тогда как Cognition показывает, что задачи с общим состоянием (код) ломаются при разделении контекста; итог 2026 года — «один главный цикл держит состояние, субагенты — stateless узкие исполнители». Harness — всё вокруг модели (промпты, инструменты, файлы памяти, права, компакция, повторы), и именно там основной инженерный рычаг.

- [обязательно] Yao et al., «ReAct: Synergizing Reasoning and Acting in Language Models» (ICLR 2023) — https://arxiv.org/abs/2210.03629 — базовый цикл; лабораторная 5 реализует его с нуля.
- [обязательно] Anthropic, «Building effective agents» (декабрь 2024) — https://www.anthropic.com/engineering/building-effective-agents — workflows vs agents и пять паттернов; самый цитируемый текст курса.
- [обязательно] Sumers, Yao, Narasimhan, Griffiths, «Cognitive Architectures for Language Agents (CoALA)» (TMLR 2024) — https://arxiv.org/abs/2309.02427 — теоретическая рамка: модули памяти, действий и принятия решений; словарь для всего курса.
- [обязательно] Cognition, «Don't Build Multi-Agents» (июнь 2025) — https://cognition.com/blog/dont-build-multi-agents и «Multi-Agents: What's Actually Working» (2026) — https://cognition.com/blog/multi-agents-working — аргумент против разделения контекста и его уточнение.
- [дополнительно] Shinn et al., «Reflexion: Language Agents with Verbal Reinforcement Learning» (NeurIPS 2023) — https://arxiv.org/abs/2303.11366 — самокритика между попытками; вторая часть лабораторной 5.
- [дополнительно] Yao et al., «Tree of Thoughts» (NeurIPS 2023) — https://arxiv.org/abs/2305.10601 ; Zhou et al., «Language Agent Tree Search (LATS)» (ICML 2024) — https://arxiv.org/abs/2310.04406 — цикл как поиск; связь с MCTS.
- [дополнительно] Anthropic, «How we built our multi-agent research system» (июнь 2025) — https://www.anthropic.com/engineering/multi-agent-research-system — orchestrator-workers в продакшне; стоимость в токенах.
- [дополнительно] Anthropic, «Effective harnesses for long-running agents» (ноябрь 2025) — https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents — harness для многочасовых задач.

---

## 6. Память и retrieval

**Что нужно понять.** Контекст конечен и не персистентен, поэтому агенту нужна внешняя память. RAG векторизует фрагменты, извлекает по близости и подставляет их в контекст; на практике гибридный поиск (BM25 + плотные эмбеддинги + reranking) стабильно превосходит чисто векторный, а «агентный RAG» позволяет модели итеративно формулировать и уточнять запросы вместо одного retrieve-then-answer. Системы памяти различают рабочую память (контекст), эпизодическую (что происходило в прошлых сессиях: траектории, рефлексии), семантическую (факты о пользователе и мире) и процедурную (навыки, инструкции). MemGPT сформулировал это как ОС: LLM сам управляет подкачкой между малым «основным контекстом» и внешним хранилищем через инструменты; Generative Agents ввели поток памяти с извлечением по recency × importance × relevance и периодической рефлексией. Память — это политика записи (что хранить, когда консолидировать) в той же мере, что и политика чтения.

- [обязательно] Lewis et al., «Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks» (NeurIPS 2020) — https://arxiv.org/abs/2005.11401 — исходная постановка RAG; достаточно разделов 2–3.
- [обязательно] Packer et al., «MemGPT: Towards LLMs as Operating Systems» (2023) — https://arxiv.org/abs/2310.08560 — иерархия памяти и управление ею через инструменты; лабораторная 6 реализует core/archival memory.
- [обязательно] Park et al., «Generative Agents: Interactive Simulacra of Human Behavior» (UIST 2023) — https://arxiv.org/abs/2304.03442 — memory stream, функция оценки извлечения, рефлексия.
- [дополнительно] Asai et al., «Self-RAG» (ICLR 2024) — https://arxiv.org/abs/2310.11511 — модель сама решает, когда извлекать и как критиковать извлечённое.
- [дополнительно] Chhikara et al., «Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory» (2025) — https://arxiv.org/abs/2504.19413 — продакшн-система памяти и её оценка.
- [дополнительно] Letta docs (memory blocks) — https://docs.letta.com/ ; LangGraph memory conceptual guide — https://langchain-ai.github.io/langgraph/concepts/memory/ — реализация трёх типов памяти в фреймворках.

---

## 7. Reasoning и планирование

**Что нужно понять.** Chain-of-thought показал, что явная выдача промежуточных шагов повышает точность на многошаговых задачах, потому что каждый порождённый токен — дополнительные вычисления, на которые модель может опереться. Reasoning-модели (o1/o3, DeepSeek-R1, Claude с extended thinking, Gemini thinking) превращают это в обученное поведение: RL с проверяемыми наградами учит модель порождать длинные «thinking»-трассы с самопроверкой и откатами, и точность масштабируется с test-time compute (бюджет размышления, параллельное сэмплирование с голосованием, поиск). Для агентов reasoning помогает на задачах с планированием, неоднозначностью, математикой и кодом и вредит по задержке и стоимости на простой маршрутизации инструментов; практически важный паттерн — interleaved thinking между вызовами инструментов. Нужно понимать рамку scaling laws (компромисс train-time vs test-time compute) и то, что «thinking budget» — настраиваемый гиперпараметр с убывающей отдачей.

- [обязательно] Wei et al., «Chain-of-Thought Prompting Elicits Reasoning in Large Language Models» (NeurIPS 2022) — https://arxiv.org/abs/2201.11903 — исходное наблюдение и его границы по размеру модели.
- [обязательно] Snell et al., «Scaling LLM Test-Time Compute Optimally Can Be More Effective Than Scaling Model Parameters» (2024) — https://arxiv.org/abs/2408.03314 — формальная постановка «compute-optimal» стратегии на инференсе; основа лабораторной 7.
- [обязательно] DeepSeek-AI, «DeepSeek-R1 incentivizes reasoning in LLMs through reinforcement learning» (Nature, сентябрь 2025; arXiv январь 2025) — https://www.nature.com/articles/s41586-025-09422-z , https://arxiv.org/abs/2501.12948 — как reasoning возникает из RL; читать вместе с темой 10.
- [дополнительно] Wang et al., «Self-Consistency Improves Chain of Thought Reasoning» (ICLR 2023) — https://arxiv.org/abs/2203.11171 — голосование по нескольким сэмплам как простейший test-time scaling.
- [дополнительно] OpenAI, «Learning to Reason with LLMs» (сентябрь 2024) — https://openai.com/index/learning-to-reason-with-llms/ — кривые масштабирования o1.
- [дополнительно] Anthropic, «Extended thinking» (документация) — https://platform.claude.com/docs/en/build-with-claude/extended-thinking — budget_tokens и interleaved thinking в API.

---

## 8. Оценка агентов и наблюдаемость

**Что нужно понять.** Агент действует много ходов и меняет внешнее состояние, поэтому оценки только финального сообщения недостаточно: нужны outcome-оценки (правильно ли конечное состояние: тесты проходят, строка в БД обновлена) и trajectory-оценки (те ли инструменты вызваны, в разумном ли порядке, без опасных действий). Сэмплирование стохастично, и один прогон ничего не значит; τ-bench ввёл pass^k — вероятность, что все k независимых прогонов успешны, — метрику надёжности, которая падает гораздо быстрее pass@k и соответствует тому, что видит пользователь в продакшне. LLM-as-judge масштабируем, но должен быть откалиброван по человеческой разметке, снабжён рубриками и имеет известные смещения (позиция, многословность, самопредпочтение). Бенчмарки (SWE-bench для кода, GAIA для общего ассистента, τ-bench для сервиса с политиками, WebArena для веба, Terminal-Bench для CLI) кодируют разные понятия «задачи»; eval-driven development означает: сначала небольшой задачно-специфичный набор, потом итерации по промптам. Наблюдаемость по OpenTelemetry GenAI semantic conventions (спаны вызовов модели, инструментов, запусков агента, счётчики токенов) — то, что делает траектории инспектируемыми.

- [обязательно] Yao et al., «τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains» (2024) — https://arxiv.org/abs/2406.12045 — pass^k и симулированный пользователь; лабораторная 8 считает pass@k и pass^k.
- [обязательно] Zheng et al., «Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena» (NeurIPS 2023) — https://arxiv.org/abs/2306.05685 — смещения судьи и методика калибровки.
- [обязательно] Anthropic, «Demystifying evals for AI agents» (январь 2026) — https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents — практическая таксономия оценок агентов.
- [обязательно] Kapoor et al., «AI Agents That Matter» (2024) — https://arxiv.org/abs/2407.01502 — почему оценка без учёта стоимости бессмысленна; Pareto-фронт точность/стоимость.
- [дополнительно] Kapoor et al., «Holistic Agent Leaderboard» (2025) — https://arxiv.org/abs/2510.11977 — 21 730 прогонов на девяти бенчмарках: граница Парето обычно крутая и разреженная, самая дорогая модель попадает на неё в 1 случае из 9, выбор обвязки меняет результат не меньше выбора модели, а анализ логов вскрывает срезанные углы.
- [дополнительно] Jimenez et al., «SWE-bench» (ICLR 2024) — https://arxiv.org/abs/2310.06770 ; Mialon et al., «GAIA» (2023) — https://arxiv.org/abs/2311.12983 ; Zhou et al., «WebArena» (2023) — https://arxiv.org/abs/2307.13854 ; Merrill et al., «Terminal-Bench» (2026) — https://arxiv.org/abs/2601.11868 — четыре разных определения «задачи»; на семинаре сравнить постановки.
- [дополнительно] Barres et al., «τ²-Bench» (2025) — https://arxiv.org/abs/2506.07982 — двусторонняя постановка, где пользователь тоже действует.
- [дополнительно] OpenTelemetry GenAI semantic conventions — https://opentelemetry.io/docs/specs/semconv/gen-ai/ — атрибуты спанов для инструментирования агента.

---

## 9. Безопасность и надёжность

**Что нужно понять.** Prompt injection — фундаментальная нерешённая уязвимость: модель не может надёжно отличить инструкции от данных в контексте, поэтому любой недоверенный контент (веб-страницы, письма, результаты инструментов) может перехватить управление агентом; для агентов опасен именно косвенный (indirect) вариант. «Смертельная триада» Уиллисона задаёт модель угроз: агент, у которого есть доступ к приватным данным, чтение недоверенного контента и канал наружу, может быть принуждён к эксфильтрации, значит хотя бы одна нога триады должна быть убрана архитектурно, а не промптом. Защиты системны: capability-based разделение потоков управления и данных (CaMeL), dual-LLM и plan-then-execute, песочницы для исполнения, минимальные привилегии, подтверждение человеком для необратимых действий. Инженерия надёжности — та же теория: вызовы инструментов должны быть идемпотентны или защищены, повторы нуждаются в backoff и бюджете, циклы — в лимитах шагов и стоимости, каждый агент — в аварийном выключателе. Списки OWASP перечисляют категории рисков: LLM Top 10 для систем, генерирующих контент; Agentic Top 10 — для систем, которые действуют.

- [обязательно] Greshake et al., «Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection» (2023) — https://arxiv.org/abs/2302.12173 — постановка indirect injection и первые атаки.
- [обязательно] Simon Willison, «The lethal trifecta for AI agents» (июнь 2025) — https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/ — модель угроз в одном абзаце; основа red-team лабораторной 9.
- [обязательно] Beurer-Kellner et al., «Design Patterns for Securing LLM Agents against Prompt Injections» (2025) — https://arxiv.org/abs/2506.08837 — шесть архитектурных паттернов защиты.
- [дополнительно] Debenedetti et al., «Defeating Prompt Injections by Design» (CaMeL, 2025) — https://arxiv.org/abs/2503.18813 — capability-based защита; формальная модель.
- [дополнительно] Debenedetti et al., «AgentDojo» (NeurIPS 2024) — https://arxiv.org/abs/2406.13352 — бенчмарк атак/защит; используется для измерения attack success rate в лабораторной.
- [дополнительно] OWASP Top 10 for LLM Applications — https://genai.owasp.org/llm-top-10/ ; OWASP Top 10 for Agentic Applications 2026 (ASI01–ASI10) — https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ — таксономия рисков для проекта.
- [дополнительно] Anthropic, Claude Code security (модель разрешений и sandboxing) — https://docs.anthropic.com/en/docs/claude-code/security — конкретная реализованная модель прав, которую можно разобрать.

---

## 10. Обучение агентов: RLHF, DPO, RLVR, GRPO, agentic RL

**Что нужно понять.** Современный post-training: предобучение → SFT на демонстрациях → оптимизация предпочтений или наград. RLHF обучает reward model на человеческих сравнениях и оптимизирует политику PPO; DPO убирает reward model, оптимизируя предпочтения напрямую (вывод через замену переменных в KL-регуляризованной задаче — студенты должны уметь его воспроизвести). RLVR заменяет человеческие предпочтения программными проверками (юнит-тесты, ответ на задачу); GRPO (DeepSeekMath/R1) убирает value network, нормализуя награды внутри группы сэмплов, — именно это дало возникновение длинного reasoning в R1-Zero. Agentic RL расширяет постановку с однократного ответа на многоходовый POMDP, где вызовы инструментов и отклики среды — внутри траектории (Kimi K2, приёмы DAPO, SWE-RL). Практический вывод: дообучение под агентов редко оправдано — frontier-модели уже RL-обучены на использовании инструментов, узкое место почти всегда harness/контекст/инструменты, данные траекторий дороги, а дообученные модели теряют общность; дообучать стоит только для узкого, высоконагруженного, критичного по стоимости и задержке tool use с проверяемыми наградами.

- [обязательно] Ouyang et al., «Training language models to follow instructions with human feedback» (InstructGPT, 2022) — https://arxiv.org/abs/2203.02155 — трёхстадийный конвейер, ставший стандартом.
- [обязательно] Rafailov et al., «Direct Preference Optimization» (NeurIPS 2023) — https://arxiv.org/abs/2305.18290 — вывод целевой функции; разобрать на семинаре.
- [обязательно] Shao et al., «DeepSeekMath» (GRPO, 2024) — https://arxiv.org/abs/2402.03300 — GRPO как есть, разделы 4–5; лабораторная 10 использует GRPOTrainer.
- [дополнительно] Yu et al., «DAPO: An Open-Source LLM Reinforcement Learning System at Scale» (2025) — https://arxiv.org/abs/2503.14476 — инженерные приёмы, без которых GRPO не сходится на масштабе.
- [дополнительно] Zhang et al., «The Landscape of Agentic Reinforcement Learning for LLMs: A Survey» (сентябрь 2025) — https://arxiv.org/abs/2509.02547 — обзор постановок многоходового RL.
- [дополнительно] Wei et al., «SWE-RL» (2025) — https://arxiv.org/abs/2502.18449 — RL на реальных репозиториях с проверяемой наградой; Llama3-SWE-RL-70B решает 41.0% SWE-bench Verified.
- [дополнительно] Qi et al., «WebRL: Training LLM Web Agents via Self-Evolving Online Curriculum Reinforcement Learning» (2024) — https://arxiv.org/abs/2411.02337 — Llama-3.1-8B на WebArena-Lite с 4.8% до 42.4%, выше GPT-4-Turbo (17.6%); пример того, как RL закрывает разрыв между открытыми и закрытыми моделями в агентных задачах.
- [дополнительно] Lambert, *RLHF Book* — https://rlhfbook.com/ — учебник ко всей теме.

---

## Инженерные посты Anthropic / OpenAI / Cognition / Manus / HumanLayer

Хронологический список текстов, которые задают текущую инженерную практику. Не научные статьи, но именно на них построены лабораторные по harness и context engineering.

**Anthropic**
- «Building effective agents» (декабрь 2024) — https://www.anthropic.com/engineering/building-effective-agents
- «How we built our multi-agent research system» (июнь 2025) — https://www.anthropic.com/engineering/multi-agent-research-system
- «Writing effective tools for AI agents — using AI agents» (сентябрь 2025) — https://www.anthropic.com/engineering/writing-tools-for-agents
- «Effective context engineering for AI agents» (сентябрь 2025) — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- «Building agents with the Claude Agent SDK» (2025) — https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk — цикл gather context → act → verify.
- «Effective harnesses for long-running agents» (ноябрь 2025) — https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- «Code execution with MCP: building more efficient agents» (ноябрь 2025) — https://www.anthropic.com/engineering/code-execution-with-mcp
- «Advanced tool use» (2025) — https://www.anthropic.com/engineering/advanced-tool-use
- «Demystifying evals for AI agents» (январь 2026) — https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- «Harness design for long-running application development» (24 марта 2026) — https://www.anthropic.com/engineering/harness-design-long-running-apps — Planner / Generator / Evaluator, sprint contracts.

**OpenAI**
- «Harness engineering: leveraging Codex in an agent-first world» (11 февраля 2026) — https://openai.com/index/harness-engineering/ — AGENTS.md как оглавление, а не энциклопедия; «легибельность» логов и метрик для агента.
- «Codex as a platform» (20 августа 2026) — https://developers.openai.com/blog/codex-as-a-platform и «Unlocking the Codex harness» — https://openai.com/index/unlocking-the-codex-harness/ — открытый исходный код harness: `codex exec`, SDK, `app-server`.

**Cognition**
- «Don't Build Multi-Agents» (июнь 2025) — https://cognition.com/blog/dont-build-multi-agents
- «Multi-Agents: What's Actually Working» (2026) — https://cognition.com/blog/multi-agents-working

**Manus**
- «Context Engineering for AI Agents: Lessons from Building Manus» (июль 2025) — https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus

**HumanLayer и другие**
- HumanLayer, «12-Factor Agents» — https://github.com/humanlayer/12-factor-agents — владей промптами, контекстом и потоком управления; человек — через вызов инструмента.
- HumanLayer, «Skill Issue: Harness Engineering for Coding Agents» — https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents — harness engineering как подмножество context engineering через точки конфигурации (CLAUDE.md/AGENTS.md, hooks, skills, subagents, MCP).
- Addy Osmani, «Agent Harness Engineering» — https://addyosmani.com/blog/agent-harness-engineering/ — обзорный текст; список ссылок: https://github.com/ai-boost/awesome-harness-engineering

---

## Спецификации и документация

**Протоколы и открытые форматы**
- MCP, спецификация 2026-07-28 — https://modelcontextprotocol.io/specification/latest ; пост о релизе — https://blog.modelcontextprotocol.io/posts/2026-07-28/ — stateless core, MRTR, Tasks; deprecated: Roots, Sampling, Logging, HTTP+SSE.
- A2A (Agent2Agent), спецификация v1.0.x — https://a2a-protocol.org/latest/specification/ — Agent Card, Task, Message, Part, Artifact; с августа 2026 в Agentic AI Foundation.
- Agent Skills, спецификация SKILL.md — https://agentskills.io/specification
- AGENTS.md — https://agents.md/
- Agentic AI Foundation (Linux Foundation) — https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation

**Фреймворки**
- Google ADK (Python 2.x) — https://google.github.io/adk-docs/ ; код — https://github.com/google/adk-python ; графы — https://google.github.io/adk-docs/graphs/ ; оценка — https://google.github.io/adk-docs/evaluate/ ; A2A — https://google.github.io/adk-docs/a2a/ ; agents-cli — https://adk.dev/deploy/agent-runtime/agents-cli/
- Claude Agent SDK — https://platform.claude.com/docs/en/agent-sdk/overview ; Claude Code hooks — https://code.claude.com/docs/en/hooks
- OpenAI Agents SDK (Python) — https://openai.github.io/openai-agents-python/
- LangGraph — https://docs.langchain.com/oss/python/langgraph/overview
- Pydantic AI — https://ai.pydantic.dev/
- smolagents — https://huggingface.co/docs/smolagents/index
- Microsoft Agent Framework — https://learn.microsoft.com/en-us/agent-framework/overview/agent-framework-overview
- CrewAI — https://docs.crewai.com/

**Наблюдаемость и оценка**
- OpenTelemetry GenAI semantic conventions — https://opentelemetry.io/docs/specs/semconv/gen-ai/ ; репозиторий — https://github.com/open-telemetry/semantic-conventions-genai
- Langfuse (v4, MIT, self-hosted) — https://langfuse.com/ ; changelog v4 — https://langfuse.com/changelog/2026-08-17-langfuse-v4
- Arize Phoenix — https://github.com/Arize-ai/phoenix ; promptfoo — https://www.promptfoo.dev/ ; Braintrust — https://www.braintrust.dev/

**Бенчмарки и среды**
- SWE-bench Verified — https://www.swebench.com/
- τ²-bench — https://github.com/sierra-research/tau2-bench
- Terminal-Bench 2.x — https://www.tbench.ai/
- Gaia2 / ARE — https://huggingface.co/blog/gaia2
- WebArena — https://webarena.dev/ ; BrowseComp-Plus — https://github.com/texttron/BrowseComp-Plus
- AgentDojo — https://arxiv.org/abs/2406.13352
- Berkeley Function Calling Leaderboard — https://gorilla.cs.berkeley.edu/leaderboard.html

**Безопасность**
- OWASP Top 10 for LLM Applications — https://genai.owasp.org/llm-top-10/
- OWASP Top 10 for Agentic Applications 2026 — https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/

**Песочницы**
- E2B — https://e2b.dev/ ; Modal Sandbox — https://modal.com/docs/guide/sandbox ; Docker Sandboxes — https://www.docker.com/products/docker-sandboxes/ ; Cloudflare Sandbox SDK — https://developers.cloudflare.com/sandbox/

---

## Бесплатные курсы, откуда брать слайды и лабораторные

- Hugging Face, *Agents Course* — https://huggingface.co/learn/agents-course/en/unit0/introduction — «dummy agent» с нуля (unit 1), agentic RAG (unit 3), финальный челлендж на GAIA, бонус по observability с Langfuse. Лучший источник готовых ноутбуков для тем 4–6.
- DeepLearning.AI, *Agentic AI* (Andrew Ng, 2025) — https://www.deeplearning.ai/courses/agentic-ai/ — четыре паттерна (reflection, tool use, planning, multi-agent) без фреймворков; модуль по evals и error analysis — образец для темы 8.
- Anthropic, *Claude Platform 101* — https://academy.claude.com/courses/claude-platform-101 ; каталог — https://anthropic.skilljar.com/ ; ноутбуки — https://github.com/anthropics/courses — agent loop, tool use, MCP, skills, context management; демо harness для темы 5.
- Google × Kaggle, *5-Day AI Agents Intensive* — https://www.kaggle.com/learn-guide/5-day-agents — whitepapers по дням (архитектуры, инструменты и MCP, контекст и память, оценка и логирование, продакшн и A2A); codelabs на ADK для основного стека курса.
- UC Berkeley RDI, *Agentic AI* (Fall 2025) — https://agenticai-learning.org/f25 и *Advanced LLM Agents* (Spring 2025) — https://llmagents-learning.org/sp25 — гостевые лекции (Dawn Song и др.), видео открыты; источник докладов для семинаров по темам 7 и 10.
- CMU 11-768, *AI Agents* (Neubig & Fried, Fall 2026) — https://www.cmu-agents.com/ ; задание 1 — https://github.com/cmu-agents/assignment-1 — публичные слайды и записи; задание «Build an Agent Harness» с оценкой компакции по расходу токенов — прямой образец для нашей лабораторной по harness.
- LangChain Academy, *Introduction to LangGraph* — https://academy.langchain.com/courses/intro-to-langgraph — state graph, checkpoints, HITL, time travel, long-term memory; если LangGraph выбран как второй фреймворк.
