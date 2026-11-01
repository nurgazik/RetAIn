import AVFoundation
import SwiftUI

/// A word's card (D48): meanings in Wiktionary's order with the model's examples, the IPA and
/// a speak button, badges for AI-written and unverified words, the user's note (D59), credits.
/// Used by the word list, the capture screen and the reader's bottom sheet.
struct WordCardView: View {
    let word: Word
    /// Status buttons ("Got it — mark retained", "Delete" → "deleted", D62); nil hides them (capture screen).
    var onStatus: ((String) -> Void)?
    /// Saves the note and returns the saved word; nil makes the note read-only.
    var onNote: ((String) async throws -> Word)?

    @State private var note: String?   // as last saved from this card
    @State private var draft = ""
    @State private var editing = false
    @State private var saving = false
    @State private var noteError: String?
    @FocusState private var focused: Bool
    static let noteLimit = 1000   // the service's limit

    init(word: Word, onStatus: ((String) -> Void)? = nil, onNote: ((String) async throws -> Word)? = nil) {
        self.word = word; self.onStatus = onStatus; self.onNote = onNote
        _note = State(initialValue: word.note)
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 14) {
                header
                noteBlock
                if word.isUnverified {
                    Label("Not found in the dictionary. Check the spelling, or archive it.", systemImage: "questionmark.circle")
                        .font(.callout).foregroundStyle(.secondary)
                }
                if let card = word.card {
                    ForEach(Array(card.senses.enumerated()), id: \.offset) { i, s in sense(i + 1, s) }
                } else if !word.definition.isEmpty {
                    Text(word.definition).font(.body)
                }
                if let n = word.servings { Text("Seen in \(n) read\(n == 1 ? "" : "s")").font(.caption).foregroundStyle(.secondary) }
                actions
                credits
            }
            .padding()
        }
        .background(Color.paper)   // D70
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(alignment: .firstTextBaseline) {
                Text(word.card?.headword ?? word.word).font(.system(.largeTitle, design: .rounded).weight(.heavy))
                if let h = word.card?.headword, h != word.word { Text("from “\(word.word)”").font(.subheadline).foregroundStyle(.secondary) }
                Spacer()
                Text(word.status).chip()
            }
            HStack(spacing: 8) {
                if let ipa = word.card?.ipa, !ipa.isEmpty {
                    Text(ipa.map(\.ipa).joined(separator: "  ")).font(.callout).foregroundStyle(.secondary)
                }
                if !word.isUnverified {
                    Button { Speech.say(word.card?.headword ?? word.word) } label: { Image(systemName: "speaker.wave.2") }
                        .buttonStyle(.borderless).accessibilityLabel("Pronounce")
                }
                if word.card?.source == "model" { badge("Written by AI") }
                if word.isUnverified { badge("Unverified") }
            }
            if let r = word.rarity {  // D61: how often you'd meet it
                HStack(spacing: 6) {
                    Text(r.dots).font(.caption).foregroundStyle(.tint)
                    Text("\(r.label) · \(r.often)").font(.caption).foregroundStyle(.secondary)
                }
                .accessibilityElement(children: .combine).accessibilityLabel("\(r.label): you'd meet it \(r.often)")
                .accessibilityIdentifier("rarity")
            }
        }
    }

    /// The user's note, first under the word: it's theirs, so it outranks the dictionary.
    @ViewBuilder private var noteBlock: some View {
        if editing {
            VStack(alignment: .leading, spacing: 8) {
                TextField("A translation, an example of your own, anything", text: $draft, axis: .vertical)
                    .lineLimit(3...10).textFieldStyle(.plain).font(.hand(24, relativeTo: .body)).foregroundStyle(Color.brandText)
                    .focused($focused).noteCard(text: .hand(24, relativeTo: .body), label: nil)
                    .onChange(of: draft) { _, d in if d.count > Self.noteLimit { draft = String(d.prefix(Self.noteLimit)) } }
                    .accessibilityIdentifier("note-field")
                HStack {
                    Button("Save") { Task { await save() } }.buttonStyle(ChunkyButtonStyle(height: 44)).disabled(saving)
                        .accessibilityIdentifier("note-save")
                    Button("Cancel") { editing = false; noteError = nil }.buttonStyle(ChunkyButtonStyle(kind: .secondary, height: 44)).disabled(saving)
                    if saving { ProgressView() }
                }
                if let noteError { Text(noteError).font(.caption).foregroundStyle(.red) }
            }
            .onAppear { focused = true }
        } else if let note, !note.isEmpty {
            VStack(alignment: .leading, spacing: 0) {  // D70: a note card, the one place with ruled lines
                HStack {
                    Text("your note").font(.hand(18, relativeTo: .caption1)).foregroundStyle(Color.inkSoft)
                    Spacer()
                    if onNote != nil { Button("Edit") { draft = note; editing = true }.font(.caption.weight(.bold)).buttonStyle(.borderless) }
                }
                Text(note).font(.hand(26, relativeTo: .body)).foregroundStyle(Color.brandText)
                    .textSelection(.enabled).accessibilityIdentifier("note-text")
            }
            .noteCard()
        } else if onNote != nil {
            Button { draft = ""; editing = true } label: { Label("Add a note", systemImage: "square.and.pencil") }
                .buttonStyle(ChunkyButtonStyle(kind: .secondary, height: 44)).fixedSize().accessibilityIdentifier("note-add")
        }
    }

    private func save() async {
        guard let onNote else { return }
        saving = true; defer { saving = false }
        do { note = try await onNote(draft).note; editing = false; noteError = nil }
        catch { noteError = "Couldn't save the note. \(error.localizedDescription)" }
    }

    private func sense(_ n: Int, _ s: Card.Sense) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text("\(n).").font(.body.monospacedDigit()).foregroundStyle(.secondary)
                VStack(alignment: .leading, spacing: 4) {
                    let labels = s.tags.filter { !Self.noiseTags.contains($0) }
                    if s.pos != nil || !labels.isEmpty {
                        Text(([s.pos].compactMap { $0 } + labels).joined(separator: " · "))
                            .font(.caption.smallCaps()).foregroundStyle(.tint)
                    }
                    Text(s.gloss).font(.body)
                    ForEach(s.examples, id: \.self) { Text("“\($0)”").font(.callout.italic()).foregroundStyle(.secondary) }
                }
            }
        }
    }

    @ViewBuilder private var actions: some View {
        if let onStatus {
            HStack {
                if !word.isUnverified, word.status == "learning" {
                    Button("Got it — mark retained") { onStatus("retained") }.buttonStyle(ChunkyButtonStyle(height: 48))
                }
                Button("Delete", role: .destructive) { onStatus("deleted") }.buttonStyle(ChunkyButtonStyle(kind: .destructive, height: 48))
                    .frame(maxWidth: 110)
                    .accessibilityIdentifier("delete-word")
            }
        }
    }

    @ViewBuilder private var credits: some View {
        if let card = word.card {
            VStack(alignment: .leading, spacing: 2) {
                if card.source == "wiktionary", let s = card.sourceUrl, let url = URL(string: s) {
                    Link("Source: Wiktionary (CC BY-SA 4.0)", destination: url)
                }
                if card.senses.contains(where: { !$0.examples.isEmpty }) { Text("Examples written by AI") }
                if card.rarity != nil, let url = URL(string: "https://github.com/rspeer/wordfreq") {
                    Link("How common: wordfreq (CC BY-SA 4.0)", destination: url)
                }
            }
            .font(.caption2).foregroundStyle(.secondary).padding(.top, 6)
        }
    }

    private func badge(_ s: String) -> some View {
        Text(s).chip(fill: .highlighter.opacity(0.6))
    }

    /// Wiktionary qualifiers that read as noise on a card ("also", "usually"…).
    private static let noiseTags: Set<String> = ["also", "usually", "specifically", "broadly", "form-of", "with", "often", "sometimes"]
}

/// Apple's on-device speech for the speak button: free, offline, no per-recording credits (D48).
enum Speech {
    private static let synth = AVSpeechSynthesizer()
    static func say(_ text: String) {
        let u = AVSpeechUtterance(string: text)
        u.voice = AVSpeechSynthesisVoice(language: "en-US")
        synth.stopSpeaking(at: .immediate)
        synth.speak(u)
    }
}
