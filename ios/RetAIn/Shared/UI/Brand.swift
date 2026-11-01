import SwiftUI
import UIKit

// The notebook look (D70): cream paper, ink outlines, chunky cards and buttons that press down onto a
// solid edge; ink blue for main actions, highlighter yellow as the accent; ruled lines only on note cards.
// Every colour has a light and a dark value. Native chrome (tab bar, navigation bar, sheets) stays Apple's.

extension Color {
    private static func pair(_ light: UInt32, _ dark: UInt32) -> Color {
        Color(UIColor { $0.userInterfaceStyle == .dark ? UIColor(rgb: dark) : UIColor(rgb: light) })
    }
    static let paper = pair(0xF7F0DC, 0x1B1915)        // the screen behind everything
    static let card = pair(0xFFFCF2, 0x29261F)         // cards and the light buttons' face
    static let ink = pair(0x2B3A55, 0xD8D0BA)          // outlines and the 3D edge
    static let inkSoft = pair(0x5B6472, 0xA9A290)      // secondary text on paper
    static let brand = pair(0x2B4C7E, 0x3E64A2)        // ink blue: main buttons, fills (white text on it)
    static let brandEdge = pair(0x1B3257, 0x223A61)    // the main buttons' edge
    static let brandText = pair(0x2B4C7E, 0x9DBCF0)    // ink blue as text or line work on paper
    static let highlighter = pair(0xF5CF4A, 0xD9B43A)  // the accent: progress, highlights, tape
    static let onHighlighter = pair(0x1E2A3B, 0x1B1915) // text on highlighter: dark in both modes
    static let margin = pair(0xE3A19B, 0x8C4A45)       // a note card's red margin line
    static let ruled = pair(0xC9D8E6, 0x3A4555)        // a note card's ruled lines
}

extension UIColor {
    convenience init(rgb: UInt32) {
        self.init(red: CGFloat(rgb >> 16 & 0xFF) / 255, green: CGFloat(rgb >> 8 & 0xFF) / 255,
                  blue: CGFloat(rgb & 0xFF) / 255, alpha: 1)
    }
}

/// A chunky button: the face sits on a solid edge 4 pt below it and presses down onto it.
struct ChunkyButtonStyle: ButtonStyle {
    enum Kind { case primary, secondary }
    var kind: Kind = .primary
    var height: CGFloat = 54
    @Environment(\.isEnabled) private var enabled

    func makeBody(configuration: Configuration) -> some View {
        let pressed = configuration.isPressed
        let face: Color = kind == .primary ? .brand : .card
        let edge: Color = kind == .primary ? .brandEdge : .ink
        let shape = RoundedRectangle(cornerRadius: 16, style: .continuous)
        return configuration.label
            .font(.system(.headline, design: .rounded).weight(.heavy))
            .foregroundStyle(kind == .primary ? Color.white : Color.ink)
            .frame(maxWidth: .infinity, minHeight: height)
            .background(face, in: shape)
            .overlay(shape.strokeBorder(edge, lineWidth: 2))
            .offset(y: pressed ? 4 : 0)
            .background(shape.fill(edge).offset(y: 4))
            .padding(.bottom, 4)
            .opacity(enabled ? 1 : 0.45)
            .animation(.spring(response: 0.18, dampingFraction: 0.6), value: pressed)
            .sensoryFeedback(.impact(weight: .light), trigger: pressed) { _, now in now }
    }
}

extension View {
    /// A paper card: the card face, an ink outline and a thicker bottom edge, like a chunky button at rest.
    func paperCard(radius: CGFloat = 18, edge: CGFloat = 4) -> some View {
        let shape = RoundedRectangle(cornerRadius: radius, style: .continuous)
        return background(Color.card, in: shape)
            .overlay(shape.strokeBorder(Color.ink, lineWidth: 2))
            .background(shape.fill(Color.ink).offset(y: edge))
            .padding(.bottom, edge)
    }

    /// A note card (D70: the only place with ruled lines): lined paper, a red margin, a strip of tape.
    /// The content is padded clear of the margin; `line` is the ruled spacing (match the text's line height).
    func noteCard(line: CGFloat = 30) -> some View {
        padding(.leading, 40).padding(.trailing, 14).padding(.vertical, 10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background {
                Canvas { g, size in
                    var y = line + 8
                    while y < size.height - 2 {
                        g.fill(Path(CGRect(x: 0, y: y, width: size.width, height: 1)), with: .color(.ruled))
                        y += line
                    }
                    g.fill(Path(CGRect(x: 28, y: 0, width: 2, height: size.height)), with: .color(.margin))
                }
            }
            .paperCard(radius: 14)
            .overlay(alignment: .top) {
                Rectangle().fill(Color.highlighter.opacity(0.75))
                    .frame(width: 64, height: 18)
                    .rotationEffect(.degrees(-4))
                    .offset(x: -70, y: -9)
                    .accessibilityHidden(true)
            }
    }
}

/// A chunky progress bar: an ink-outlined track filled with highlighter.
struct InkProgress: View {
    let value: Double
    let total: Double

    var body: some View {
        GeometryReader { geo in
            let share = total > 0 ? min(max(value / total, 0), 1) : 0
            ZStack(alignment: .leading) {
                Capsule().fill(Color.card)
                Capsule().fill(Color.highlighter).frame(width: max(geo.size.width * share, share > 0 ? 14 : 0))
                Capsule().strokeBorder(Color.ink, lineWidth: 2)
            }
        }
        .frame(height: 14)
        .animation(.spring(response: 0.4, dampingFraction: 0.8), value: value)
        .accessibilityElement()
        .accessibilityValue("\(Int(value)) of \(Int(total))")
    }
}
