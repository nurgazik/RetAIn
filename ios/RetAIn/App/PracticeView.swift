import SwiftUI

/// Daily practice (D53, D56; diagrams/flow-fill-in-the-word.md, flow-write-a-sentence.md).
/// Order: a fill-in for every word first (quick recall), then a sentence for every word (production),
/// then a summary where words can be marked retained.
enum PracticeStep: Equatable {
    case fill(Int), write(Int), summary   // index into the set's items

    /// The next unanswered exercise; fill-ins (where the word has one) come before any writing.
    static func next(_ items: [PracticeItem]) -> PracticeStep {
        if let i = items.firstIndex(where: { $0.fill != nil && $0.attempts.fill == nil && $0.status == "learning" }) { return .fill(i) }
        if let i = items.firstIndex(where: { $0.attempts.write == nil && $0.status == "learning" }) { return .write(i) }
        return .summary
    }
    /// Exercises done / total, for the progress bar.
    static func progress(_ items: [PracticeItem]) -> (done: Int, total: Int) {
        let live = items.filter { $0.status == "learning" || $0.attempts.write != nil }
        let total = live.reduce(0) { $0 + ($1.fill == nil ? 1 : 2) }
        let done = live.reduce(0) { $0 + ($1.attempts.fill == nil ? 0 : 1) + ($1.attempts.write == nil ? 0 : 1) }
        return (done, total)
    }
}

struct PracticeView: View {
    @State private var set: PracticeSet?
    @State private var error: String?
    @State private var loading = false
    @State private var shown: PracticeStep?          // what's on screen (stays while a result is shown)
    @State private var answer = ""
    @State private var fillResult: FillResult?
    @State private var writeResult: WriteResult?
    @State private var busy = false
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
        } else {
            let step = shown ?? PracticeStep.next(set.items)
            let p = PracticeStep.progress(set.items)
            VStack(spacing: 0) {
                ProgressView(value: Double(p.done), total: Double(max(p.total, 1)))
                    .padding(.horizontal).padding(.top, 4)
                ScrollView {
                    switch step {
                    case .fill(let i): fillCard(set.items[i])
                    case .write(let i): writeCard(set.items[i])
                    case .summary: summary(set)
                    }
                }
                .scrollDismissesKeyboard(.interactively)
            }
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
            }
            if let error = inputError { Text(error).font(.callout).foregroundStyle(.red) }
        }
        .padding()
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

    // MARK: summary

    private func summary(_ set: PracticeSet) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            Label("Done for today", systemImage: "checkmark.seal.fill").font(.title2.bold()).foregroundStyle(.green)
            Text("Words you got right come back later; misses come back tomorrow.").foregroundStyle(.secondary)
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
        .onAppear { if !PracticeReminder.asked { PracticeReminder.asked = true; askReminder = true } }
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
            if s.day != set?.day { shown = nil; fillResult = nil; writeResult = nil; answer = "" }
            set = s; error = nil
        } catch { if set == nil { self.error = error.localizedDescription } }
    }

    private func submitFill(_ item: PracticeItem) async {
        busy = true; defer { busy = false }
        do {
            let r = try await RetAInClient.shared.practiceFill(wordId: item.wordId, answer: answer)
            fillResult = r; inputError = nil; shown = PracticeStep.next(set?.items ?? [])
            update(item.wordId) { $0.attempts.fill = .init(correct: r.correct ? 1 : 0, verdict: nil, reason: nil, fix: nil, answer: answer) }
        } catch { inputError = error.localizedDescription }
    }

    private func submitWrite(_ item: PracticeItem) async {
        busy = true; defer { busy = false }
        do {
            let r = try await RetAInClient.shared.practiceWrite(wordId: item.wordId, sentence: answer)
            writeResult = r; inputError = nil; shown = PracticeStep.next(set?.items ?? [])
            update(item.wordId) { $0.attempts.write = .init(correct: nil, verdict: r.verdict, reason: r.reason, fix: r.fix, answer: answer) }
        } catch APIError.http(422, let message) { inputError = message }
        catch { inputError = error.localizedDescription }
    }

    private func advance() {
        fillResult = nil; writeResult = nil; answer = ""; inputError = nil; shown = nil
    }

    private func retain(_ item: PracticeItem) async {
        guard (try? await RetAInClient.shared.setWordStatus(item.wordId, "retained")) != nil else { return }
        update(item.wordId) { $0.status = "retained" }
    }

    private func update(_ wordId: Int, _ change: (inout PracticeItem) -> Void) {
        guard let i = set?.items.firstIndex(where: { $0.wordId == wordId }) else { return }
        change(&set!.items[i])
    }
}
