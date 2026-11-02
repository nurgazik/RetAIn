import SwiftUI
import WidgetKit

/// What the Words list shows and in what order (D71); both remembered between launches.
enum WordsShow: String, CaseIterable {
    case all, learning, retained
    var label: String { ["all": "All", "learning": "Learning", "retained": "Retained"][rawValue]! }
}
enum WordsSort: String, CaseIterable {
    case az, newest, oldest
    var label: String { ["az": "A–Z", "newest": "Newest first", "oldest": "Oldest first"][rawValue]! }
}

struct WordsView: View {
    /// Set by a widget tap (retain://word/<id>): open that word's card once the list is loaded.
    @Binding var openWordId: Int?
    @State private var words: [Word] = []
    @State private var path: [Word] = []
    @State private var newWord = ""
    @State private var error: String?
    @State private var busy = false
    @State private var query = ""      // search (App/WordSearch.swift); it looks across all words, whatever the filter
    @AppStorage("wordsShow") private var show: WordsShow = .all
    @AppStorage("wordsSort") private var sort: WordsSort = .az
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        NavigationStack(path: $path) {
            List {
                if searching { searchResults } else { allWords }
                if let error { Text(error).foregroundStyle(.red).font(.caption) }
            }
            .notebookList()   // D70: paper behind, cream rows; native swipe, search and refresh
            .searchable(text: $query, placement: .navigationBarDrawer(displayMode: .always),
                        prompt: "Search words, meanings, notes")
            .autocorrectionDisabled().textInputAutocapitalization(.never)
            .navigationTitle("Words")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {  // D71: one standard menu instead of controls in the list
                    Menu {
                        Section("Show") {  // buttons with a tick, so each section keeps its heading
                            ForEach(WordsShow.allCases, id: \.self) { o in
                                Button { show = o } label: { if show == o { Label(o.label, systemImage: "checkmark") } else { Text(o.label) } }
                            }
                        }
                        Section("Sort by") {
                            ForEach(WordsSort.allCases, id: \.self) { o in
                                Button { sort = o } label: { if sort == o { Label(o.label, systemImage: "checkmark") } else { Text(o.label) } }
                            }
                        }
                    } label: {  // filled while anything but the default is on, so a hidden filter isn't forgotten
                        Image(systemName: show == .all && sort == .az ? "line.3.horizontal.decrease.circle"
                                                                      : "line.3.horizontal.decrease.circle.fill")
                    }
                    .accessibilityLabel("Show and sort").accessibilityIdentifier("words-filter")
                }
            }
            .navigationDestination(for: Word.self) { w in
                WordCardView(word: w, onStatus: { status in Task { await set(w, status); path.removeAll() } },
                             onNote: { text in let saved = try await RetAInClient.shared.setNote(w.id, text); await load(); return saved })
            }
            .onChange(of: openWordId, initial: true) { _, _ in openPending() }
            .onChange(of: words) { _, _ in openPending() }
            .refreshable { await load() }
            .task { await load() }
            .onChange(of: scenePhase) { _, phase in if phase == .active { Task { await load() } } }
        }
    }

    private var searching: Bool { !WordSearch.fold(query).isEmpty }

    @ViewBuilder private var allWords: some View {
        Section {
            HStack {
                TextField("Add a word", text: $newWord).textInputAutocapitalization(.never).autocorrectionDisabled()
                    .onSubmit { Task { await add(newWord) } }
                Button("Add") { Task { await add(newWord) } }.disabled(newWord.trimmingCharacters(in: .whitespaces).isEmpty || busy)
                    .buttonStyle(ChunkyButtonStyle(height: 36)).frame(width: 76)
            }
            .listRowBackground(Color.card)
        }
        if groups.isEmpty, !words.isEmpty {
            Text(show == .retained ? "No retained words yet." : "No words here.").foregroundStyle(Color.inkSoft)
                .listRowBackground(Color.card)
        }
        ForEach(groups, id: \.0) { status, list in
            Section("\(status) · \(list.count)") {
                ForEach(list) { w in row(w, nil) }
            }
            .listRowBackground(Color.card)
        }
    }

    /// Ranked hits (exact, starts with, a form of it, contains, your note, a meaning, a near-miss
    /// spelling); "Add" when the query isn't a saved word, so searching first also avoids duplicates.
    @ViewBuilder private var searchResults: some View {
        let hits = WordSearch.results(words, query)
        let typed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        if hits.isEmpty {
            addRow(typed, hits)
            ContentUnavailableView.search(text: typed)
        } else {  // results first: a misspelling shouldn't sit above the word it probably means
            Section("\(hits.count) result\(hits.count == 1 ? "" : "s")") {
                ForEach(hits) { h in row(h.word, h) }
            }
            .listRowBackground(Color.card)
            addRow(typed, hits)
        }
    }

    /// No "Add" when the word is already saved, or saved in its dictionary form (the server would fold
    /// "bolstered" into "bolster" anyway, D58).
    @ViewBuilder private func addRow(_ typed: String, _ hits: [WordSearch.Hit]) -> some View {
        if !WordSearch.hasExact(words, typed), !hits.contains(where: { $0.tier == 2 }), !typed.contains(" ") {
            Section {
                Button { Task { await add(typed) } } label: {
                    HStack { Label("Add “\(typed.lowercased())”", systemImage: "plus.circle"); if busy { Spacer(); ProgressView() } }
                }
                .disabled(busy).accessibilityIdentifier("search-add")
            }
            .listRowBackground(Color.card)
        }
    }

    private func row(_ w: Word, _ hit: WordSearch.Hit?) -> some View {
        NavigationLink(value: w) {
            VStack(alignment: .leading) {
                HStack {
                    Text(highlighted(w.word)).font(.body.weight(.bold))
                    if let r = w.rarity { Text(r.dots).font(.caption2).foregroundStyle(.secondary).accessibilityLabel(r.label) }
                    if let n = w.servings, n > 0 { Text("· \(n)").foregroundStyle(.secondary).font(.caption) }
                    if w.isUnverified { Text("Unverified").font(.caption2).foregroundStyle(.orange) }
                    if w.note?.isEmpty == false { Image(systemName: "note.text").font(.caption).foregroundStyle(.secondary).accessibilityLabel("Has a note") }
                    if hit != nil, w.status == "retained" { Text("retained").font(.caption2).foregroundStyle(.green) }
                }
                switch hit?.field {
                case .note?: Text("Your note: " + highlighted(hit?.snippet ?? "")).font(.caption).foregroundStyle(.secondary).lineLimit(2)
                case .meaning?: Text(highlighted(hit?.snippet ?? "")).font(.caption).foregroundStyle(.secondary).lineLimit(2)
                default: Text(w.firstDefinition).font(.caption).foregroundStyle(.secondary).lineLimit(1)
                }
            }
        }
        .swipeActions(edge: .trailing) {
            Button("Delete", role: .destructive) { Task { await set(w, "deleted") } }
            if w.status != "retained" { Button("Retained") { Task { await set(w, "retained") } }.tint(.green) }
            if w.status != "learning" { Button("Learn again") { Task { await set(w, "learning") } }.tint(.orange) }  // D71: starts over
        }
    }

    /// The search terms in bold, ignoring case and accents (the same rules as matching).
    private func highlighted(_ text: String) -> AttributedString {
        var out = AttributedString(text)
        guard searching else { return out }
        for term in WordSearch.fold(query).split(separator: " ") {
            var from = out.startIndex
            while let r = out[from...].range(of: String(term), options: [.caseInsensitive, .diacriticInsensitive]) {
                out[r].inlinePresentationIntent = .stronglyEmphasized
                from = r.upperBound
            }
        }
        return out
    }

    private var groups: [(String, [Word])] { Self.groups(words, show: show, sort: sort) }

    /// Learning, then retained (or just one of them), each sorted A–Z ignoring case and accents, or by when
    /// it was saved (the id breaks same-day ties). Search keeps its own ranking (D63).
    static func groups(_ words: [Word], show: WordsShow = .all, sort: WordsSort = .az) -> [(String, [Word])] {
        let statuses = show == .all ? ["learning", "retained"] : [show.rawValue]
        return statuses.compactMap { s in  // deleted words never come back from the server (D62)
            let l = words.filter { $0.status == s }.sorted { a, b in
                switch sort {
                case .az: return a.word.localizedStandardCompare(b.word) == .orderedAscending
                case .newest: return (a.added, a.id) > (b.added, b.id)
                case .oldest: return (a.added, a.id) < (b.added, b.id)
                }
            }
            return l.isEmpty ? nil : (s, l)
        }
    }
    private func openPending() {
        guard let id = openWordId, let w = words.first(where: { $0.id == id }) else { return }
        path = [w]; openWordId = nil
    }
    private func load() async {
        do {
            words = try await RetAInClient.shared.words(); error = nil
            WordsStore.replaceAll(words); WidgetCenter.shared.reloadAllTimelines()
        } catch { self.error = error.localizedDescription }
    }
    private func add(_ text: String) async {
        let w = text.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !w.isEmpty else { return }
        busy = true; defer { busy = false }
        do { _ = try await RetAInClient.shared.addWord(w); newWord = ""; await load() } catch { self.error = error.localizedDescription }
    }
    private func set(_ w: Word, _ status: String) async {
        do {
            if status == "deleted" { _ = try await RetAInClient.shared.deleteWord(w.id) }
            else { _ = try await RetAInClient.shared.setWordStatus(w.id, status) }
            await load()
        } catch { self.error = error.localizedDescription }
    }
}
