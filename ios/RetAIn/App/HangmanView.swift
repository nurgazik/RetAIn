import SwiftUI

/// Hangman (D69): guess the word letter by letter from its meaning, with 6 lives, the same for every
/// word so games compare. The phone plays; the finished game's guess log goes to the server, which
/// re-checks it, stores it (stats, later leaderboards) and counts it on the schedule.
struct HangmanGame: Equatable {
    static let lives = 6
    static let keys = Array("abcdefghijklmnopqrstuvwxyz")
    let word: String
    private(set) var guesses: [Character] = []

    private var chars: [Character] { Array(word.lowercased()) }
    var letters: Set<Character> { Set(chars.filter(Self.keys.contains)) }
    var wrong: Int { guesses.filter { !letters.contains($0) }.count }
    var won: Bool { letters.isSubset(of: guesses) }
    var lost: Bool { wrong >= Self.lives }
    var over: Bool { won || lost }
    /// A keyboard letter (spaces, hyphens and the like are shown from the start).
    func isKey(_ i: Int) -> Bool { Self.keys.contains(chars[i]) }
    func shown(_ i: Int) -> Bool { !isKey(i) || guesses.contains(chars[i]) }

    /// → whether the letter is in the word; repeats and guesses after the end are ignored.
    @discardableResult mutating func guess(_ c: Character) -> Bool {
        guard !over, !guesses.contains(c) else { return false }
        guesses.append(c)
        return letters.contains(c)
    }
}

struct HangmanCard: View {
    let item: PracticeItem
    let onFinish: (HangmanGame, Bool, Double) async -> Void  // the game, hint used, seconds
    let onOpenCard: () -> Void
    let onNext: () -> Void

    @State private var game: HangmanGame
    @State private var hinted = false
    @State private var started = Date()
    @State private var finishing = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    init(item: PracticeItem, onFinish: @escaping (HangmanGame, Bool, Double) async -> Void,
         onOpenCard: @escaping () -> Void, onNext: @escaping () -> Void) {
        self.item = item; self.onFinish = onFinish; self.onOpenCard = onOpenCard; self.onNext = onNext
        _game = State(initialValue: HangmanGame(word: item.word))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                Text("HANGMAN").font(.caption.bold()).foregroundStyle(.secondary)
                Spacer()
                lives
            }
            tiles.frame(maxWidth: .infinity)
            Text("Meaning: \(item.definition)").font(.callout).foregroundStyle(.secondary)
            if game.over {
                result
            } else if hinted, let text = item.fill?.text {
                Text(text).font(.system(.body, design: .serif)).fontDesign(.serif).padding(12)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .paperCard(radius: 14, edge: 2)
            } else if item.fill != nil {
                Button { hinted = true } label: { Label("Show a sentence", systemImage: "lightbulb").frame(maxWidth: .infinity) }
                    .buttonStyle(ChunkyButtonStyle(kind: .secondary)).accessibilityIdentifier("hangman-hint")
            }
            keyboard
        }
        .padding()
    }

    // MARK: pieces

    private var lives: some View {
        HStack(spacing: 4) {
            ForEach(0..<HangmanGame.lives, id: \.self) { i in
                Image(systemName: "sparkle")
                    .foregroundStyle(i < HangmanGame.lives - game.wrong ? Color.highlighter : Color.inkSoft.opacity(0.3))
            }
        }
        .font(.callout)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(HangmanGame.lives - game.wrong) lives left")
    }

    /// The word's cells over the shared stardust tiles (D65); wrong guesses thicken the mist.
    private var tiles: some View {
        let shown = Array(item.word)
        let n = shown.count
        let cell: CGFloat = n <= 9 ? 30 : n <= 12 ? 24 : 18
        return HStack(spacing: 3) {
            ForEach(0..<n, id: \.self) { i in
                ZStack {
                    Text("Mg").fixedSize().hidden()  // a line's height, so cells sit like text
                    if game.shown(i) || game.lost {
                        Text(String(shown[i])).fixedSize()
                            .foregroundStyle(game.won ? Color.brandText : game.shown(i) ? Color.primary : .red)
                            .transition(.scale(scale: 0.2).combined(with: .opacity))
                    }
                }
                .frame(width: cell)
            }
        }
        .font(.system(size: cell * 0.9, weight: game.won ? .bold : .regular, design: .serif)).fontDesign(.serif)
        .background {
            Stardust(empty: (0..<n).map { game.isKey($0) && !game.shown($0) && !game.lost },
                     tiles: (0..<n).map(game.isKey), cell: cell, gutter: 3,
                     mist: Double(game.wrong) / Double(HangmanGame.lives), still: reduceMotion)
        }
        .animation(.spring(response: 0.3, dampingFraction: 0.55), value: game.guesses)
        .keyframeAnimator(initialValue: 0.0, trigger: game.wrong) { view, x in
            view.offset(x: reduceMotion ? 0 : x)
        } keyframes: { _ in
            KeyframeTrack {
                CubicKeyframe(-10, duration: 0.06)
                CubicKeyframe(9, duration: 0.08)
                CubicKeyframe(-6, duration: 0.08)
                CubicKeyframe(0, duration: 0.1)
            }
        }
        .sensoryFeedback(.error, trigger: game.wrong)
        .sensoryFeedback(.success, trigger: game.won)
        .contentShape(Rectangle())
        .onTapGesture { if game.over { onOpenCard() } }  // the word's card, as in fill-in (D65)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(game.over ? item.word : "\(n) letters")
        .accessibilityIdentifier("hangman-word")
    }

    private var result: some View {
        VStack(alignment: .leading, spacing: 12) {
            let wrong = game.wrong
            Label(game.won ? "Got it" + (wrong > 0 ? " · \(wrong) wrong guess\(wrong == 1 ? "" : "es")" : "") : "Out of lives",
                  systemImage: game.won ? "checkmark.circle.fill" : "xmark.circle.fill")
                .font(.headline).foregroundStyle(game.won ? .green : .red)
            Text("Tap the word to see its card.").font(.caption).foregroundStyle(.secondary)
            Button { onNext() } label: { Text("Next").frame(maxWidth: .infinity) }
                .buttonStyle(ChunkyButtonStyle()).disabled(finishing)
        }
        .accessibilityIdentifier("hangman-result")
    }

    private var keyboard: some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 6), count: 7), spacing: 8) {
            ForEach(HangmanGame.keys, id: \.self) { c in
                let used = game.guesses.contains(c), hit = game.letters.contains(c)
                Button { tap(c) } label: {
                    Text(String(c).uppercased()).font(.system(.title3, design: .rounded).weight(.heavy))
                        .frame(maxWidth: .infinity, minHeight: 44)
                        .foregroundStyle(used ? (hit ? Color.onHighlighter : Color.inkSoft.opacity(0.5)) : Color.ink)
                }
                .buttonStyle(KeyStyle(state: used ? (hit ? .hit : .miss) : .open))
                .disabled(used || game.over || finishing)
                .accessibilityIdentifier("hangman-key-\(c)")
            }
        }
    }

    private func tap(_ c: Character) {
        game.guess(c)
        guard game.over else { return }
        finishing = true
        Task { await onFinish(game, hinted, Date().timeIntervalSince(started)); finishing = false }
    }
}

/// A hangman key (D70): a small chunky key; a right letter turns highlighter, a wrong one goes flat.
private struct KeyStyle: ButtonStyle {
    enum State { case open, hit, miss }
    let state: State

    func makeBody(configuration: Configuration) -> some View {
        let shape = RoundedRectangle(cornerRadius: 10, style: .continuous)
        let raised = state != .miss
        let down = configuration.isPressed || !raised
        return configuration.label
            .background(state == .hit ? Color.highlighter : state == .miss ? Color.paper : Color.card, in: shape)
            .overlay(shape.strokeBorder(Color.ink.opacity(raised ? 1 : 0.25), lineWidth: 1.5))
            .offset(y: down ? 3 : 0)
            .background(shape.fill(Color.ink.opacity(raised ? 1 : 0)).offset(y: 3))
            .padding(.bottom, 3)
            .animation(.spring(response: 0.15, dampingFraction: 0.6), value: configuration.isPressed)
    }
}
