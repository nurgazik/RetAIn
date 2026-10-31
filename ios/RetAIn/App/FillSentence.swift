import SwiftUI

/// The fill-in sentence with a live gap (D65): one misty, stardusted tile per letter of the answer; typed
/// letters condense out of the dust, with no judgment while typing. A wrong try shakes the gap and shows
/// the wrong word in red (tap: its meaning, D58); a right one shows the word bold in the brand colour
/// (tap: its card). Words and gap wrap
/// together (FlowLayout), so the gap is a real view with a real width and can't hang off a line end.
struct FillSentence: View {
    enum Gap: Equatable { case typing(String), wrong(String), solved(String) }
    let text: String            // the sentence with "_____" where the word goes
    let letters: Int
    let gap: Gap
    var misses = 0              // wrong tries so far: each new one shakes the gap
    var active = false          // the keyboard is up: a caret blinks in the next cell
    var onTapWrong: () -> Void = {}
    var onTapSolved: () -> Void = {}

    @ScaledMetric(relativeTo: .title3) private var space: CGFloat = 5

    var body: some View {
        FlowLayout(spacing: space, lineSpacing: 6) {
            ForEach(Array(text.split(separator: " ").enumerated()), id: \.offset) { _, token in
                if let blank = token.range(of: "_____") {  // punctuation stays glued to the gap: "_____,"
                    HStack(alignment: .firstTextBaseline, spacing: 0) {
                        Text(token[..<blank.lowerBound])
                        LetterGap(letters: letters, gap: gap, misses: misses, active: active,
                                  onTapWrong: onTapWrong, onTapSolved: onTapSolved)
                        Text(token[blank.upperBound...])
                    }
                } else {
                    Text(token)
                }
            }
        }
        .font(.system(.title3, design: .serif))
    }
}

/// The gap itself: letter cells over stardust while typing, or the wrong / solved word.
private struct LetterGap: View {
    let letters: Int
    let gap: FillSentence.Gap
    let misses: Int
    let active: Bool
    let onTapWrong: () -> Void
    let onTapSolved: () -> Void
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @ScaledMetric(relativeTo: .title3) private var cell: CGFloat = 16
    private let gutter: CGFloat = 2

    var body: some View {
        content
            .padding(.horizontal, 2)
            .keyframeAnimator(initialValue: 0.0, trigger: misses) { view, x in
                view.offset(x: reduceMotion ? 0 : x)
            } keyframes: { _ in
                KeyframeTrack {
                    CubicKeyframe(-10, duration: 0.06)
                    CubicKeyframe(9, duration: 0.08)
                    CubicKeyframe(-6, duration: 0.08)
                    CubicKeyframe(3, duration: 0.08)
                    CubicKeyframe(0, duration: 0.1)
                }
            }
            .sensoryFeedback(.error, trigger: misses)
            .sensoryFeedback(.success, trigger: solved)
    }

    private var solved: Bool { if case .solved = gap { true } else { false } }

    @ViewBuilder private var content: some View {
        switch gap {
        case .solved(let word):
            Text(word).bold().foregroundStyle(Color.brand)   // tap: the word's card
                .onTapGesture(perform: onTapSolved)
                .accessibilityIdentifier("solved-word")
                .accessibilityAddTraits(.isButton)
                .transition(.scale(scale: 0.7).combined(with: .opacity))
        case .wrong(let word):
            Text(word).foregroundStyle(.red).underline()
                .onTapGesture(perform: onTapWrong)
                .accessibilityAddTraits(.isButton)
        case .typing(let typed):
            let chars = Array(typed)
            HStack(alignment: .firstTextBaseline, spacing: gutter) {
                ForEach(0..<max(letters, chars.count), id: \.self) { i in
                    ZStack {
                        Text("Mg").fixedSize().hidden()  // a line's height and baseline, so cells sit on the text
                        if i < chars.count {
                            Text(String(chars[i])).fixedSize()
                                .transition(.asymmetric(insertion: .scale(scale: 0.2).combined(with: .opacity),
                                                        removal: .opacity))
                        }
                    }
                    .frame(width: cell)
                }
            }
            .background {
                Stardust(cells: letters, filled: chars.count, cell: cell, gutter: gutter, caret: active, still: reduceMotion)
            }
            .animation(.spring(response: 0.3, dampingFraction: 0.55), value: typed)
        }
    }
}

/// A misty tile per letter, text-high, so the gap reads as "type here"; empty tiles shimmer with dust,
/// the next one glows brighter and carries a blinking caret while the keyboard is up. One Canvas;
/// particle positions are fixed per cell (seeded), only brightness and a slight drift move.
private struct Stardust: View {
    let cells: Int
    let filled: Int
    let cell: CGFloat
    let gutter: CGFloat
    let caret: Bool
    let still: Bool             // Reduce Motion: a still frame, a steady caret

    var body: some View {
        TimelineView(.animation(minimumInterval: 1 / 30, paused: still)) { timeline in
            let t = still ? 0 : timeline.date.timeIntervalSinceReferenceDate
            Canvas { g, size in
                let ink = GraphicsContext.Shading.color(.brand)
                for i in 0..<cells {  // a tile under every letter, typed or not
                    let next = i == filled
                    var tile = g
                    tile.opacity = next ? 0.2 : 0.1
                    tile.fill(Path(roundedRect: CGRect(x: CGFloat(i) * (cell + gutter), y: size.height * 0.06,
                                                       width: cell, height: size.height * 0.88), cornerRadius: 4), with: ink)
                }
                if caret, filled < cells, still || Int(t * 2) % 2 == 0 {
                    let x = CGFloat(filled) * (cell + gutter) + 2
                    g.fill(Path(CGRect(x: x, y: size.height * 0.18, width: 1.5, height: size.height * 0.64)), with: ink)
                }
                for i in filled..<max(cells, filled) {
                    let left = CGFloat(i) * (cell + gutter)
                    let next = i == filled
                    for k in 0..<(next ? 12 : 9) {
                        let r = { (n: Int) in Self.noise(i, k * 7 + n) }
                        let x = left + cell * (0.12 + 0.76 * r(1)) + sin(t * 0.7 + 6.3 * r(2)) * 1.2
                        let y = size.height * (0.28 + 0.58 * r(3)) + cos(t * 0.6 + 6.3 * r(4)) * 1.2
                        let radius = 0.6 + 1.0 * r(5)
                        var dot = g
                        dot.opacity = min(1, (0.2 + 0.65 * (0.5 + 0.5 * sin(t * (1.4 + 2.2 * r(6)) + 6.3 * r(7)))) * (next ? 1.3 : 1))
                        dot.fill(Path(ellipseIn: CGRect(x: x - radius, y: y - radius, width: radius * 2, height: radius * 2)),
                                 with: ink)
                    }
                }
            }
        }
        .accessibilityHidden(true)
    }

    /// A fixed pseudo-random number in 0..<1 for (cell, n): same dust every frame and every launch.
    private static func noise(_ i: Int, _ n: Int) -> Double {
        let x = sin(Double(i * 127 + n * 311) * 12.9898) * 43758.5453
        return x - x.rounded(.down)
    }
}

/// Lays views out left to right, wrapping to a new line when the next one doesn't fit; each line's
/// views share a text baseline, like words in a paragraph.
struct FlowLayout: Layout {
    var spacing: CGFloat
    var lineSpacing: CGFloat

    private struct Line {
        var items: [(index: Int, x: CGFloat, baseline: CGFloat)] = []
        var y: CGFloat = 0, width: CGFloat = 0, ascent: CGFloat = 0, descent: CGFloat = 0
    }

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let lines = arrange(subviews, width: proposal.width ?? .infinity)
        let last = lines.last.map { $0.y + $0.ascent + $0.descent } ?? 0
        return CGSize(width: lines.map(\.width).max() ?? 0, height: last)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        for line in arrange(subviews, width: bounds.width) {
            for item in line.items {
                subviews[item.index].place(at: CGPoint(x: bounds.minX + item.x, y: bounds.minY + line.y + line.ascent - item.baseline),
                                           proposal: .unspecified)
            }
        }
    }

    private func arrange(_ subviews: Subviews, width: CGFloat) -> [Line] {
        var lines = [Line()]
        for (index, view) in subviews.enumerated() {
            let d = view.dimensions(in: .unspecified)
            let baseline = d[.firstTextBaseline]
            if !lines[lines.count - 1].items.isEmpty, lines[lines.count - 1].width + spacing + d.width > width {
                let above = lines[lines.count - 1]
                lines.append(Line(y: above.y + above.ascent + above.descent + lineSpacing))
            }
            var line = lines[lines.count - 1]
            let x = line.items.isEmpty ? 0 : line.width + spacing
            line.items.append((index, x, baseline))
            line.width = x + d.width
            line.ascent = max(line.ascent, baseline)
            line.descent = max(line.descent, d.height - baseline)
            lines[lines.count - 1] = line
        }
        return lines
    }
}
