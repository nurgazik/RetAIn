import SwiftUI
import WidgetKit

struct TodaysWordsView: View {
    let entry: TodaysWordsEntry
    var body: some View {
        Group {
            switch entry.state {
            case .noCache: message("Open RetAIn to load your words")
            case .noLearning: message("No words in learning")
            case let .word(w, i, n):
                VStack(alignment: .leading, spacing: 4) {
                    HStack(alignment: .firstTextBaseline) {
                        Text(w.word).font(.title2.weight(.semibold)).lineLimit(1).minimumScaleFactor(0.7)
                        if let pos = w.pos { Text(pos).font(.caption.smallCaps()).foregroundStyle(.secondary) }
                        Spacer()
                    }
                    Text(w.firstDefinition).font(.subheadline).foregroundStyle(.secondary).lineLimit(3)
                    if let more = w.card.map({ $0.senses.count - 1 }), more > 0 {
                        Text("+\(more) more meaning\(more == 1 ? "" : "s")").font(.caption2).foregroundStyle(.tertiary)
                    }
                    Spacer(minLength: 0)
                    HStack {
                        Text("Today's words · \(i + 1) / \(n)").font(.caption).foregroundStyle(.secondary).monospacedDigit()
                        Spacer()
                        if n > 1 {
                            Button(intent: NextWordIntent()) { Image(systemName: "chevron.right") }
                                .buttonStyle(.bordered).buttonBorderShape(.circle)
                        }
                    }
                }
                .widgetURL(WordLink.url(w.id))  // tap anywhere but the chevron: open this word in the app
            }
        }
        .containerBackground(.fill.tertiary, for: .widget)
    }
    private func message(_ s: String) -> some View {
        Text(s).font(.subheadline).foregroundStyle(.secondary).frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
