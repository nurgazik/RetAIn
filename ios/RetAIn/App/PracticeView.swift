import SwiftUI

/// Daily practice (D53, D56, D57; diagrams/flow-fill-in-the-word.md, flow-write-a-sentence.md).
/// Opens on a chooser: the user picks fill-in or sentences, in any order, and may skip either (D57).
/// Today's words and their results sit under the two choices, with Mark retained per word.
enum PracticeExercise: Equatable {
    case fill, write

    /// Whether this word still has this exercise to do today.
    func pending(_ item: PracticeItem) -> Bool {
        guard item.status == "learning" else { return false }
        switch self {
        case .fill: return item.fill != nil && item.attempts.fill == nil
        case .write: return item.attempts.write == nil
        }
    }
    private func done(_ item: PracticeItem) -> Bool {
        self == .fill ? item.attempts.fill != nil : item.attempts.write != nil
    }

    /// The next word to do in this exercise, if any.
    func next(_ items: [PracticeItem]) -> Int? { items.firstIndex(where: pending) }

    /// Done / total for this exercise; words retained before they were tried drop out.
    func progress(_ items: [PracticeItem]) -> (done: Int, total: Int) {
        let counted = items.filter { pending($0) || done($0) }
        return (counted.filter(done).count, counted.count)
    }
}

struct PracticeView: View {
    @State private var set: PracticeSet?
    @State private var error: String?
    @State private var loading = false
    @State private var exercise: PracticeExercise?   // nil: the chooser
    @State private var shown: Int?                   // the word on screen (stays while a result is shown)
    @State private var answer = ""
    @State private var fillResult: FillResult?
    @State private var writeResult: WriteResult?
    @State private var busy = false
    @State private var hinting = false
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
            .alert("Remind you to practise each day?", isPresented: $askReminder) {
                Button("Remind me at 7 pm") { Task { await PracticeReminder.enable() } }
                Button("Not now", role: .cancel) {}
            } message: { Text("A short daily nudge. You can turn it off in Settings.") }
        }
    }

    @ViewBuilder private func content(_ set: PracticeSet) -> some View {
        if set.items.isEmpty {
            ContentUnavailableView("Nothing to practise", systemImage: "checkmark.seal",
                                   description: Text("Add words in the Words tab, or come back when some are due."))
        } else if let exercise, let i = shown ?? exercise.next(set.items) {
            let p = exercise.progress(set.items)
            VStack(spacing: 0) {
                ProgressView(value: Double(p.done), total: Double(max(p.total, 1)))
                    .padding(.horizontal).padding(.top, 4)
                ScrollView {
                    switch exercise {
                    case .fill: fillCard(set.items[i])
                    case .write: writeCard(set.items[i])
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
            label("Fill in the word", item.fill?.source == "read" ? "From one of your reads" : nil)
            Text(blanked(item.fill?.text ?? "", answer: fillResult.map { $0.expected }))
                .font(.system(.title3, design: .serif)).lineSpacing(4)
            Text("Meaning: \(item.definition)").font(.callout).foregroundStyle(.secondary)
            if let r = fillResult {
                resultBanner(ok: r.correct, title: r.correct ? "Correct" : "The word was “\(r.expected)”", detail: r.note)
                nextButton()
            } else {
                TextField("Type the word", text: $answer)
                    .focused($typing)
                    .textInputAutocapitalization(.never).autocorrectionDisabled()
                    .textFieldStyle(.roundedBorder).font(.title3)
                    .onSubmit { Task { await submitFill(item) } }
                checkButton(disabled: answer.trimmingCharacters(in: .whitespaces).isEmpty) { await submitFill(item) }
                if let options = item.fill?.hint { hintPills(item, options) }
                else { hintButton(item) }
            }
            if let error = inputError { Text(error).font(.callout).foregroundStyle(.red) }
        }
        .padding()
    }

    /// D58: the word among lookalikes; tapping one is the same as typing it and tapping Check.
    private func hintPills(_ item: PracticeItem, _ options: [String]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Which one fits?").font(.caption).foregroundStyle(.secondary)
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                ForEach(options, id: \.self) { option in
                    Button { answer = option; typing = false; Task { await submitFill(item) } } label: {
                        Text(option).font(.system(.body, design: .serif)).lineLimit(1).minimumScaleFactor(0.7)
                            .frame(maxWidth: .infinity).padding(.vertical, 10)
                    }
                    .buttonStyle(.bordered).buttonBorderShape(.capsule).disabled(busy)
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
        .buttonStyle(.bordered).controlSize(.large).disabled(hinting || busy)
    }

    // MARK: write a sentence

    private func writeCard(_ item: PracticeItem) -> some View {
        VStack(alignment: .leading, spacing: 16) {
            label("Use it in a sentence", nil)
            Text(item.word).font(.system(.largeTitle, design: .serif)).bold().accessibilityIdentifier("practice-word")
            Text(item.definition).font(.callout).foregroundStyle(.secondary)
            if let r = writeResult {
                Text(answer).font(.system(.body, design: .serif)).padding(10)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(.quaternary.opacity(0.5), in: .rect(cornerRadius: 8))
                verdictBanner(r)
                nextButton()
            } else {
                TextField("Write your own sentence with “\(item.word)”", text: $answer, axis: .vertical)
                    .focused($typing)
                    .lineLimit(3...6).textFieldStyle(.roundedBorder).font(.system(.body, design: .serif))
                checkButton(disabled: answer.split(separator: " ").count < 3) { await submitWrite(item) }
                Text("Dictation works too: tap the mic on the keyboard.").font(.caption).foregroundStyle(.secondary)
            }
            if let error = inputError { Text(error).font(.callout).foregroundStyle(.red) }
        }
        .padding()
    }

    private func verdictBanner(_ r: WriteResult) -> some View {
        let (title, color, icon): (String, Color, String) = switch r.verdict {
        case "natural": ("Natural", .green, "checkmark.circle.fill")
        case "wrong": ("Not quite right", .red, "xmark.circle.fill")
        default: ("Could be better", .orange, "exclamationmark.circle.fill")
        }
        return VStack(alignment: .leading, spacing: 8) {
            Label(title, systemImage: icon).font(.headline).foregroundStyle(color)
            if let reason = r.reason, !reason.isEmpty { Text(reason).font(.callout) }
            if let fix = r.fix, !fix.isEmpty {
                Text("Try: ").font(.callout).bold() + Text(fix).font(.system(.callout, design: .serif))
            }
        }
        .padding(12).frame(maxWidth: .infinity, alignment: .leading)
        .background(color.opacity(0.1), in: .rect(cornerRadius: 10))
    }

    // MARK: chooser

    private func chooser(_ set: PracticeSet) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            if PracticeExercise.fill.next(set.items) == nil && PracticeExercise.write.next(set.items) == nil {
                Label("Done for today", systemImage: "checkmark.seal.fill").font(.title2.bold()).foregroundStyle(.green)
            }
            exerciseCard(.fill, "Fill in the word", "Recall it from a sentence", set.items)
            exerciseCard(.write, "Use it in a sentence", "Write your own", set.items)
            Text("TODAY'S WORDS").font(.caption.bold()).foregroundStyle(.secondary).padding(.top, 8)
            Text("Words you got right come back later; misses come back tomorrow.").font(.callout).foregroundStyle(.secondary)
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
                        Button("Mark retained") { Task { await retain(item) } }.buttonStyle(.bordered).font(.caption)
                    }
                }
                Divider()
            }
        }
        .padding()
    }

    private func exerciseCard(_ kind: PracticeExercise, _ title: String, _ subtitle: String,
                              _ items: [PracticeItem]) -> some View {
        let p = kind.progress(items)
        let left = p.total - p.done
        return Button { exercise = kind } label: {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(title).font(.headline)
                    Text(subtitle).font(.callout).foregroundStyle(.secondary)
                }
                Spacer()
                if left == 0 {
                    Label(p.total == 0 ? "None today" : "Done", systemImage: p.total == 0 ? "minus" : "checkmark")
                        .font(.callout).foregroundStyle(p.total == 0 ? Color.secondary : .green)
                } else {
                    Text("\(left) of \(p.total) left").font(.callout).foregroundStyle(.secondary)
                    Image(systemName: "chevron.right").foregroundStyle(.tertiary)
                }
            }
            .padding().frame(maxWidth: .infinity, alignment: .leading)
            .background(.quaternary.opacity(0.5), in: .rect(cornerRadius: 12))
        }
        .buttonStyle(.plain).disabled(left == 0)
    }

    private func outcome(_ item: PracticeItem) -> String {
        var parts: [String] = []
        if let f = item.attempts.fill { parts.append(f.correct == 1 ? "fill-in ✓" : "fill-in ✗") }
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
        .buttonStyle(.borderedProminent).controlSize(.large).disabled(disabled || busy)
    }

    private func nextButton() -> some View {
        Button { advance() } label: { Text("Next").frame(maxWidth: .infinity) }
            .buttonStyle(.borderedProminent).controlSize(.large)
    }

    private func resultBanner(ok: Bool, title: String, detail: String?) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Label(title, systemImage: ok ? "checkmark.circle.fill" : "xmark.circle.fill").font(.headline)
                .foregroundStyle(ok ? .green : .red)
            if let detail { Text(detail).font(.callout) }
        }
        .padding(12).frame(maxWidth: .infinity, alignment: .leading)
        .background((ok ? Color.green : .red).opacity(0.1), in: .rect(cornerRadius: 10))
    }

    /// The sentence with a visible blank, or with the answer filled in (bold) once it's known.
    private func blanked(_ text: String, answer: String?) -> AttributedString {
        let parts = text.components(separatedBy: "_____")
        var out = AttributedString(parts.first ?? "")
        if parts.count > 1 {
            var gap = AttributedString(answer ?? "\u{2007}\u{2007}\u{2007}\u{2007}\u{2007}\u{2007}\u{2007}\u{2007}")
            gap.underlineStyle = .single
            if answer != nil { gap.inlinePresentationIntent = .stronglyEmphasized }
            out += gap + AttributedString(parts.dropFirst().joined(separator: "_____"))
        }
        return out
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
            fillResult = r; inputError = nil; shown = index(item)
            update(item.wordId) { $0.attempts.fill = .init(correct: r.correct ? 1 : 0, verdict: nil, reason: nil, fix: nil, answer: answer) }
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

    /// On to the next word in this exercise; when it's finished, back to the chooser
    /// (the reminder is offered the first time either exercise is finished).
    private func advance() {
        fillResult = nil; writeResult = nil; answer = ""; inputError = nil; shown = nil
        guard let exercise, exercise.next(set?.items ?? []) == nil else { return }
        self.exercise = nil
        if !PracticeReminder.asked { PracticeReminder.asked = true; askReminder = true }
    }

    private func leave() {
        typing = false; fillResult = nil; writeResult = nil; answer = ""; inputError = nil; shown = nil; exercise = nil
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
