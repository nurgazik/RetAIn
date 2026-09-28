import SwiftUI
import WidgetKit

/// Home-screen widget: today's learning words, one at a time, › to advance.
@main
struct RetAInWidgets: WidgetBundle {
    var body: some Widget { TodaysWordsWidget() }
}

struct TodaysWordsWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "TodaysWords", provider: TodaysWordsProvider()) { entry in
            TodaysWordsView(entry: entry)
        }
        .configurationDisplayName("Today's words")
        .description("Five of your learning words each day, with their meanings.")
        .supportedFamilies([.systemMedium])
    }
}

struct TodaysWordsEntry: TimelineEntry {
    enum State { case noCache, noLearning, word(Word, index: Int, count: Int) }
    let date: Date
    let state: State
}

struct TodaysWordsProvider: TimelineProvider {
    func placeholder(in context: Context) -> TodaysWordsEntry { .sample }
    func getSnapshot(in context: Context, completion: @escaping (TodaysWordsEntry) -> Void) {
        let e = current(); if context.isPreview, case .noCache = e.state { completion(.sample) } else { completion(e) }
    }
    func getTimeline(in context: Context, completion: @escaping (Timeline<TodaysWordsEntry>) -> Void) {
        let midnight = Calendar.current.startOfDay(for: .now.addingTimeInterval(86_400))
        completion(Timeline(entries: [current()], policy: .after(midnight)))
    }

    private func current() -> TodaysWordsEntry {
        guard let all = WordsStore.load() else { return .init(date: .now, state: .noCache) }
        let day = WordsStore.dayKey()
        let today = WordsStore.todaysWords(from: all, day: day)
        guard !today.isEmpty else { return .init(date: .now, state: .noLearning) }
        let i = min(WordsStore.position(day: day), today.count - 1)
        return .init(date: .now, state: .word(today[i], index: i, count: today.count))
    }
}

extension TodaysWordsEntry {
    static let sample = TodaysWordsEntry(date: .now, state: .word(
        Word(id: 0, word: "ubiquitous", pos: "adjective", definition: "present, appearing, or found everywhere",
             status: "learning", added: "", servings: nil), index: 0, count: WordsStore.perDay))
}
