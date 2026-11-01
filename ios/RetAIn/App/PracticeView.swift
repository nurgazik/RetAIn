import SwiftUI

/// Daily practice (D53, D56, D57, D60; diagrams/flow-fill-in-the-word.md, flow-write-a-sentence.md).
/// Opens on a chooser: the user picks fill-in or sentences, in any order, and may skip either (D57).
/// One list, no limit (D66): every learning word, due ones first; the user goes as far as they like, in
/// rounds of five with a checkpoint between them. Words so far sit below, with Mark retained.
enum PracticeExercise: Equatable {
    case fill, write, hangman

    /// Whether this word still has this exercise to do today.
    func pending(_ item: PracticeItem) -> Bool {
        guard item.status == "learning" else { return false }
        switch self {
        case .fill: return item.fill != nil && item.attempts.fill == nil
        case .write: return item.attempts.write == nil
        case .hangman: return item.attempts.hangman == nil
        }
    }
    private func done(_ item: PracticeItem) -> Bool {
        switch self {
        case .fill: item.attempts.fill != nil
        case .write: item.attempts.write != nil
        case .hangman: item.attempts.hangman != nil
        }
    }

    /// The next word to do in this exercise, if any.
    func next(_ items: [PracticeItem]) -> Int? {
        items.firstIndex(where: pending)
    }

    /// Done / total for this exercise; words retained before they were tried drop out;
    /// words not yet in a round (`remaining`) count as still to do.
    func progress(_ items: [PracticeItem], remaining: Int = 0) -> (done: Int, total: Int) {
        let counted = items.filter { pending($0) || done($0) }
        return (counted.filter(done).count, counted.count + remaining)
    }
}

struct PracticeView: View {
    @State private var set: PracticeSet?
    @State private var error: String?
    @State private var loading = false
    @State private var exercise: PracticeExercise?   // nil: the chooser
    @State private var preparing = false             // a round is being prepared
    @State private var shown: Int?                   // the word on screen (stays while a result is shown)
    @State private var answer = ""
    @State private var fillResult: FillResult?
    @State private var writeResult: WriteResult?
    @State private var busy = false
    @State private var hinting = false
    @State private var misses = 0                    // wrong fill-in tries on this word: each shakes the gap (D65)
    @State private var meaningShown: PracticeItem.Wrong?
    @State private var card: Word?                   // the solved word's card, opened from the gap (D65)
    @State private var inputError: String?
    @State private var askReminder = false
    @FocusState private var typing: Bool
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        NavigationStack {
            Group {
                if let set { content(set) }
                else if let error { ContentUnavailableView("Couldn't load practice", systemImage: "wifi.exclamationmark", description: Text(error)) }
                else { ProgressView("Preparing today's words…") }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color.paper.ignoresSafeArea())   // D70: cream paper behind every screen
            .navigationTitle("Practice")
            .toolbar {
                if exercise != nil {
                    ToolbarItem(placement: .topBarLeading) {
                        Button { leave() } label: { Label("Exercises", systemImage: "chevron.left").labelStyle(.titleAndIcon) }
                    }
                }
            }
            .task { await load() }
            .onChange(of: scenePhase) { _, p in if p == .active, set != nil { Task { await load() } } }
            .sheet(item: $card) { w in  // as the reader's word sheet (D48)
                WordCardView(word: w, onStatus: { status in Task { await cardStatus(w, status) } }, onNote: { text in
                    let saved = try await RetAInClient.shared.setNote(w.id, text)
                    update(w.id) { $0.note = saved.note }
                    return saved
                })
                .presentationDetents([.medium, .large])
                .presentationDragIndicator(.visible)
            }
            .alert("Remind you to practise each day?", isPresented: $askReminder) {
                Button("Remind me at 7 pm") { Task { await PracticeReminder.enable() } }
                Button("Not now", role: .cancel) {}
            } message: { Text("A short daily nudge. You can turn it off in Settings.") }
        }
    }

    @ViewBuilder private func content(_ set: PracticeSet) -> some View {
        if set.items.isEmpty && set.left == 0 {
            ContentUnavailableView("Nothing to practise", systemImage: "checkmark.seal",
                                   description: Text("Add words in the Words tab, or come back when some are due."))
        } else if let exercise, shown == nil, exercise.next(set.items) == nil, set.left > 0 {
            checkpoint(set)
        } else if let exercise, let i = shown ?? exercise.next(set.items) {
            let p = exercise.progress(set.items, remaining: set.left)
            VStack(spacing: 0) {
                InkProgress(value: Double(p.done), total: Double(max(p.total, 1)))
                    .padding(.horizontal).padding(.top, 4)
                ScrollView {
                    switch exercise {
                    case .fill: fillCard(set.items[i])
                    case .write: writeCard(set.items[i])
                    case .hangman: hangmanCard(set.items[i])
                    }
                }
                .scrollDismissesKeyboard(.interactively)
            }
        } else {
            ScrollView { chooser(set) }
        }
    }

    // MARK: fill in the word

    private func fillCard(_ item: PracticeItem) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            label("Fill in the word", nil)
            let lastWrong = item.fill?.wrong?.last
            // D65: the gap is the input; a hidden field behind it takes the typing. D70: sentence + meaning on a paper card
            VStack(alignment: .leading, spacing: 14) {
            FillSentence(text: item.fill?.text ?? "", letters: item.fill?.letters ?? 8, gap: gap(lastWrong),
                         misses: misses, active: typing, onTapWrong: { meaningShown = lastWrong },
                         onTapSolved: { Task { await openCard(item) } })
                .id(item.wordId)
                .frame(maxWidth: .infinity, alignment: .leading)
                .contentShape(Rectangle())
                .onTapGesture { if fillResult == nil { typing = true } }
                .background {
                    TextField("Type the word", text: $answer)
                        .focused($typing)
                        .textInputAutocapitalization(.never).autocorrectionDisabled()
                        .onSubmit { Task { await submitFill(item) } }
                        .foregroundStyle(.clear).tint(.clear)  // no text or caret of its own: the gap shows it
                        .frame(width: 1, height: 1).clipped().opacity(0.02)
                        .accessibilityIdentifier("fill-input")
                }
                .task(id: item.wordId) { if fillResult == nil { typing = true } }
                .popover(item: $meaningShown) { w in
                    VStack(alignment: .leading, spacing: 6) {
                        Text(w.answer).font(.system(.title3, design: .serif)).fontDesign(.serif).bold()
                        Text(w.meaning ?? "No dictionary meaning for this word.").font(.callout)
                    }
                    .padding().frame(maxWidth: 320, alignment: .leading)
                    .presentationCompactAdaptation(.popover)
                }
            Text("Meaning: \(item.definition)").font(.callout).foregroundStyle(Color.inkSoft)
            }
            .padding(16)
            .paperCard()
            if let r = fillResult {
                resultBanner(ok: true, title: "Correct", detail: r.note)
                yourNote(item)   // only once solved: the note may hold the word itself
                nextButton()
            } else {
                if lastWrong != nil {
                    Text("Not quite: try again. Tap the red word to see what it means.").font(.callout).foregroundStyle(.red)
                }
                checkButton(disabled: answer.trimmingCharacters(in: .whitespaces).isEmpty) { await submitFill(item) }
                if let options = item.fill?.hint { hintPills(item, options) }
                else { hintButton(item) }
            }
            if let error = inputError { Text(error).font(.callout).foregroundStyle(.red) }
        }
        .padding()
    }

    /// The user's own note on the word (D59), as on its card.
    @ViewBuilder private func yourNote(_ item: PracticeItem) -> some View {
        if let note = item.note, !note.isEmpty {
            VStack(alignment: .leading, spacing: 0) {  // D70: a note card, the one place with ruled lines
                Text("your note").font(.hand(18, relativeTo: .caption1)).foregroundStyle(Color.inkSoft)
                Text(note).font(.hand(26, relativeTo: .body)).foregroundStyle(Color.brandText)
            }
            .noteCard()
            .accessibilityElement(children: .combine)
            .accessibilityIdentifier("practice-note")
        }
    }

    /// D58: the word among lookalikes; tapping one is the same as typing it and tapping Check.
    private func hintPills(_ item: PracticeItem, _ options: [String]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Which one fits?").font(.caption).foregroundStyle(.secondary)
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                ForEach(options, id: \.self) { option in
                    let tried = item.fill?.wrong?.contains { $0.answer == option.lowercased() } ?? false
                    Button { answer = option; typing = false; Task { await submitFill(item) } } label: {
                        Text(option).font(.system(.body, design: .serif)).fontDesign(.serif).lineLimit(1).minimumScaleFactor(0.7)
                            .strikethrough(tried).frame(maxWidth: .infinity).padding(.vertical, 10)
                    }
                    .buttonStyle(ChunkyButtonStyle(kind: .secondary, height: 46)).disabled(busy || tried)
                    .accessibilityIdentifier("hint-option")
                }
            }
        }
    }

    private func hintButton(_ item: PracticeItem) -> some View {
        Button { Task { await askHint(item) } } label: {
            HStack { if hinting { ProgressView().padding(.trailing, 4) }; Label("Hint", systemImage: "lightbulb") }
                .frame(maxWidth: .infinity)
        }
        .buttonStyle(ChunkyButtonStyle(kind: .secondary)).disabled(hinting || busy)
    }

    // MARK: hangman (D69)

    private func hangmanCard(_ item: PracticeItem) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            HangmanCard(item: item, onFinish: { game, hint, seconds in await submitHangman(item, game, hint, seconds) },
                        onOpenCard: { Task { await openCard(item) } }, onNext: advance)
                .id(item.wordId)
            if let error = inputError { Text(error).font(.callout).foregroundStyle(.red).padding(.horizontal) }
        }
    }

    // MARK: write a sentence

    private func writeCard(_ item: PracticeItem) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            label("Use it in a sentence", nil)
            Text(item.word).font(.system(.largeTitle, design: .serif)).fontDesign(.serif).bold().accessibilityIdentifier("practice-word")
            Text(item.definition).font(.callout).foregroundStyle(.secondary)
            yourNote(item)
            if let r = writeResult {
                Text(answer).font(.system(.body, design: .serif)).fontDesign(.serif).padding(12)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .paperCard(radius: 14, edge: 2)
                verdictBanner(r)
                nextButton()
            } else {
                TextField("Write your own sentence with “\(item.word)”", text: $answer, axis: .vertical)
                    .focused($typing)
                    .lineLimit(3...6).textFieldStyle(.plain).font(.system(.body, design: .serif)).fontDesign(.serif)
                    .padding(12).paperCard(radius: 14, edge: 2)
                checkButton(disabled: answer.split(separator: " ").count < 3) { await submitWrite(item) }
                Text("Dictation works too: tap the mic on the keyboard.").font(.caption).foregroundStyle(.secondary)
            }
            if let error = inputError { Text(error).font(.callout).foregroundStyle(.red) }
        }
        .padding()
    }

    /// D68: the verdict is about the word's meaning and usage only; when that's right, the corrected sentence
    /// is grammar polish ("Polished:"), not a mistake; otherwise it's the usage fix ("Try:").
    private func verdictBanner(_ r: WriteResult) -> some View {
        let (title, color, icon): (String, Color, String) = switch r.verdict {
        case "natural": ("Meaning correct", .green, "checkmark.circle.fill")
        case "wrong": ("Not quite right", .red, "xmark.circle.fill")
        default: ("Could be better", .orange, "exclamationmark.circle.fill")
        }
        return VStack(alignment: .leading, spacing: 8) {
            Label(title, systemImage: icon).font(.headline).foregroundStyle(color)
            if let reason = r.reason, !reason.isEmpty { Text(reason).font(.callout) }
            if let fix = r.fix, !fix.isEmpty {
                Text(r.verdict == "natural" ? "Polished: " : "Try: ").font(.callout).bold()
                    + Text(fix).font(.system(.callout, design: .serif)).fontDesign(.serif)
            }
        }
        .padding(12).frame(maxWidth: .infinity, alignment: .leading)
        .paperCard(radius: 16)
    }

    // MARK: chooser

    private func chooser(_ set: PracticeSet) -> some View {
        let words = set.wordProgress
        return VStack(alignment: .leading, spacing: 14) {
            Text("YOUR WORDS").font(.caption.bold()).foregroundStyle(.secondary)
            if set.isDone {
                Label("Every word practised today · \(words.total)", systemImage: "checkmark.seal.fill")
                    .font(.title3.bold()).foregroundStyle(.green)
            } else {
                Text("\(words.done) of \(words.total) words practised today · due words come first")
                    .font(.callout).foregroundStyle(.secondary)
                InkProgress(value: Double(words.done), total: Double(words.total)).accessibilityIdentifier("today-progress")
                exerciseCard(.fill, "Fill in the word", "Recall it from a sentence", set)
                exerciseCard(.write, "Use it in a sentence", "Write your own", set)
                exerciseCard(.hangman, "Hangman", "Guess it letter by letter", set)
                if !set.withoutFill.isEmpty {  // D66: say so rather than count them as done
                    Text("No fill-in sentence today for \(set.withoutFill.map(\.word).joined(separator: ", ")): try \(set.withoutFill.count == 1 ? "it" : "them") in a sentence.")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            if let error = inputError { Text(error).font(.callout).foregroundStyle(.red) }
            if !set.items.isEmpty {
                Text("WORDS SO FAR TODAY").font(.caption.bold()).foregroundStyle(.secondary).padding(.top, 8)
                Text("Words you got right come back later; misses come back tomorrow.").font(.callout).foregroundStyle(.secondary)
            }
            ForEach(set.items) { item in
                HStack(alignment: .firstTextBaseline) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(item.word).font(.headline)
                        Text(outcome(item)).font(.caption).foregroundStyle(.secondary)
                    }
                    Spacer()
                    if item.status == "retained" {
                        Label("Retained", systemImage: "checkmark").font(.caption).foregroundStyle(.green)
                    } else {
                        Button("Mark retained") { Task { await retain(item) } }
                            .buttonStyle(ChunkyButtonStyle(kind: .secondary, height: 34)).frame(width: 150)
                    }
                }
                Divider()
            }
        }
        .padding()
    }

    /// Between rounds (D60): the next five, or back to the exercises.
    private func checkpoint(_ set: PracticeSet) -> some View {
        let left = set.left
        return VStack(spacing: 16) {
            Label("Round done", systemImage: "flag.checkered").font(.title2.bold())
            Text("\(left) more word\(left == 1 ? "" : "s") on your list")
                .font(.callout).foregroundStyle(.secondary)
            Button { Task { await nextRound() } } label: {
                HStack { if preparing { ProgressView().padding(.trailing, 4) }; Text("Next round") }.frame(maxWidth: .infinity)
            }
            .buttonStyle(ChunkyButtonStyle()).disabled(preparing).accessibilityIdentifier("next-round")
            Button { leave() } label: { Text("Back to exercises").frame(maxWidth: .infinity) }
                .buttonStyle(ChunkyButtonStyle(kind: .secondary))
            if let error = inputError { Text(error).font(.callout).foregroundStyle(.red) }
        }
        .padding().frame(maxHeight: .infinity)
    }

    private func exerciseCard(_ kind: PracticeExercise, _ title: String, _ subtitle: String,
                              _ set: PracticeSet) -> some View {
        let p = kind.progress(set.items, remaining: set.left)
        let left = p.total - p.done
        return Button { Task { await start(kind) } } label: {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(title).font(.headline)
                    Text(subtitle).font(.callout).foregroundStyle(.secondary)
                }
                Spacer()
                if preparing {
                    ProgressView()
                } else if left == 0 {
                    Label(p.total == 0 ? "None today" : "Done", systemImage: p.total == 0 ? "minus" : "checkmark")
                        .font(.callout).foregroundStyle(p.total == 0 ? Color.secondary : .green)
                } else {
                    Text("\(left) of \(p.total) left").font(.callout).foregroundStyle(.secondary)
                    Image(systemName: "chevron.right").foregroundStyle(.tertiary)
                }
            }
            .padding().frame(maxWidth: .infinity, alignment: .leading)
            .paperCard()
        }
        .buttonStyle(.plain).disabled(left == 0 || preparing)
    }

    private func outcome(_ item: PracticeItem) -> String {
        var parts: [String] = []
        if let f = item.attempts.fill { parts.append(f.correct == 1 ? "fill-in ✓" : "fill-in ✗") }
        if let h = item.attempts.hangman { parts.append(h.correct == 1 ? "hangman ✓" : "hangman ✗") }
        if let w = item.attempts.write {
            parts.append(["natural": "sentence ✓", "wrong": "sentence ✗"][w.verdict ?? ""] ?? "sentence: could be better")
        }
        return parts.joined(separator: " · ")
    }

    // MARK: pieces

    private func label(_ title: String, _ sub: String?) -> some View {
        HStack {
            Text(title.uppercased()).font(.caption.bold()).foregroundStyle(.secondary)
            if let sub { Spacer(); Text(sub).font(.caption).foregroundStyle(.secondary) }
        }
    }

    private func checkButton(disabled: Bool, _ action: @escaping () async -> Void) -> some View {
        Button { typing = false; Task { await action() } } label: {
            HStack { if busy { ProgressView().padding(.trailing, 4) }; Text("Check") }.frame(maxWidth: .infinity)
        }
        .buttonStyle(ChunkyButtonStyle()).disabled(disabled || busy)
    }

    private func nextButton() -> some View {
        Button { advance() } label: { Text("Next").frame(maxWidth: .infinity) }
            .buttonStyle(ChunkyButtonStyle())
    }

    private func resultBanner(ok: Bool, title: String, detail: String?) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Label(title, systemImage: ok ? "checkmark.circle.fill" : "xmark.circle.fill").font(.headline)
                .foregroundStyle(ok ? .green : .red)
            if let detail { Text(detail).font(.callout) }
        }
        .padding(12).frame(maxWidth: .infinity, alignment: .leading)
        .paperCard(radius: 16)
    }

    /// What the gap shows: the word once solved (bold); the last wrong try in red until the user types
    /// again (tap: its meaning, D58); otherwise what's typed so far, over the dust.
    private func gap(_ lastWrong: PracticeItem.Wrong?) -> FillSentence.Gap {
        if let r = fillResult { return .solved(r.expected ?? answer) }
        if answer.isEmpty, let w = lastWrong { return .wrong(w.answer) }
        return .typing(answer)
    }

    // MARK: actions

    private func load() async {
        guard !loading else { return }
        loading = true; defer { loading = false }
        do {
            let s = try await RetAInClient.shared.practiceToday()
            if s.day != set?.day { exercise = nil; shown = nil; fillResult = nil; writeResult = nil; answer = "" }
            set = s; error = nil
        } catch { if set == nil { self.error = error.localizedDescription } }
    }

    private func submitFill(_ item: PracticeItem) async {
        busy = true; defer { busy = false }
        do {
            let r = try await RetAInClient.shared.practiceFill(wordId: item.wordId, answer: answer)
            inputError = nil; shown = index(item)
            if r.correct {  // done; ✓ in the summary only if right first time (D58)
                withAnimation(.spring(response: 0.35, dampingFraction: 0.6)) { fillResult = r }
                let firstTry = item.fill?.wrong?.isEmpty ?? true
                update(item.wordId) { $0.attempts.fill = .init(correct: firstTry ? 1 : 0, verdict: nil, reason: nil, fix: nil, answer: answer) }
            } else {  // try again: the word stays hidden; the wrong one goes in the blank
                let w = PracticeItem.Wrong(answer: r.answer ?? answer.lowercased(), meaning: r.meaning)
                let tried = (item.fill?.wrong ?? []).filter { $0.answer != w.answer } + [w]
                update(item.wordId) { $0.fill?.wrong = tried }
                answer = ""; misses += 1
                if item.fill?.hint == nil { typing = true }  // straight back to typing
            }
        } catch { inputError = error.localizedDescription }
    }

    private func submitHangman(_ item: PracticeItem, _ game: HangmanGame, _ hint: Bool, _ seconds: Double) async {
        shown = index(item)  // the finished game stays on screen until Next
        do {
            let r = try await RetAInClient.shared.practiceHangman(wordId: item.wordId, guesses: game.guesses, hint: hint,
                                                                  seconds: seconds)
            inputError = nil
            update(item.wordId) { $0.attempts.hangman = .init(correct: r.won ? 1 : 0, verdict: nil, reason: nil, fix: nil,
                                                             answer: String(game.guesses)) }
        } catch { inputError = error.localizedDescription }
    }

    private func askHint(_ item: PracticeItem) async {
        hinting = true; defer { hinting = false }
        do {
            let r = try await RetAInClient.shared.practiceHint(wordId: item.wordId)
            inputError = nil
            update(item.wordId) { $0.fill?.hint = r.options }
        } catch { inputError = error.localizedDescription }
    }

    private func submitWrite(_ item: PracticeItem) async {
        busy = true; defer { busy = false }
        do {
            let r = try await RetAInClient.shared.practiceWrite(wordId: item.wordId, sentence: answer)
            writeResult = r; inputError = nil; shown = index(item)
            update(item.wordId) { $0.attempts.write = .init(correct: nil, verdict: r.verdict, reason: r.reason, fix: r.fix, answer: answer) }
        } catch APIError.http(422, let message) { inputError = message }
        catch { inputError = error.localizedDescription }
    }

    /// On to the next word in this exercise; at the end of a round with more to come, the checkpoint;
    /// when the list is finished, back to the chooser (the reminder is offered the first time).
    private func advance() {
        fillResult = nil; writeResult = nil; answer = ""; inputError = nil; shown = nil; misses = 0
        guard let exercise, exercise.next(set?.items ?? []) == nil else { return }
        if (set?.left ?? 0) > 0 { return }  // the checkpoint shows
        self.exercise = nil
        if !PracticeReminder.asked { PracticeReminder.asked = true; askReminder = true }
    }

    /// Into an exercise; with nothing ready, the next round is prepared first.
    private func start(_ kind: PracticeExercise) async {
        inputError = nil
        if kind.next(set?.items ?? []) == nil, (set?.left ?? 0) > 0 {
            guard await nextRound() else { return }
        }
        exercise = kind
    }

    @discardableResult private func nextRound() async -> Bool {
        preparing = true; defer { preparing = false }
        do { set = try await RetAInClient.shared.practiceRound(); inputError = nil; return true }
        catch { inputError = error.localizedDescription; return false }
    }

    private func leave() {
        typing = false; fillResult = nil; writeResult = nil; answer = ""; inputError = nil; shown = nil; exercise = nil; misses = 0
    }

    /// The word's full card, from the user's word list (cards aren't part of the practice set).
    private func openCard(_ item: PracticeItem) async {
        do { card = try await RetAInClient.shared.words().first { $0.id == item.wordId }; inputError = nil }
        catch { inputError = error.localizedDescription }
    }

    /// Mark retained or Delete from the card: as on the Words tab; a deleted word leaves today's set (D62).
    private func cardStatus(_ w: Word, _ status: String) async {
        card = nil
        if status == "deleted" {
            guard (try? await RetAInClient.shared.deleteWord(w.id)) != nil else { return }
            advance(); await load()
        } else if (try? await RetAInClient.shared.setWordStatus(w.id, status)) != nil {
            update(w.id) { $0.status = status }
        }
    }

    private func index(_ item: PracticeItem) -> Int? { set?.items.firstIndex { $0.wordId == item.wordId } }

    private func retain(_ item: PracticeItem) async {
        guard (try? await RetAInClient.shared.setWordStatus(item.wordId, "retained")) != nil else { return }
        update(item.wordId) { $0.status = "retained" }
    }

    private func update(_ wordId: Int, _ change: (inout PracticeItem) -> Void) {
        guard let i = set?.items.firstIndex(where: { $0.wordId == wordId }) else { return }
        change(&set!.items[i])
    }
}
