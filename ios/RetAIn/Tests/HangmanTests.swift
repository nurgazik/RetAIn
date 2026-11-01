import XCTest
@testable import RetAIn

/// Hangman's rules (D69); the server replays the same log the same way (practice.hangman_result).
final class HangmanTests: XCTestCase {
    func testAWinShowsEveryOccurrence() {
        var g = HangmanGame(word: "assuage")
        XCTAssertTrue(g.guess("s"))
        XCTAssertEqual((0..<7).filter(g.shown), [1, 2])
        for c in "zauge" { g.guess(c) }
        XCTAssertTrue(g.won); XCTAssertEqual(g.wrong, 1)
        XCTAssertFalse(g.guess("q"))  // over: ignored
        XCTAssertEqual(g.guesses.count, 6)
    }

    func testSixWrongLoses() {
        var g = HangmanGame(word: "gait")
        for c in "bcdefh" { g.guess(c) }
        XCTAssertTrue(g.lost); XCTAssertFalse(g.won); XCTAssertEqual(g.wrong, HangmanGame.lives)
    }

    func testRepeatsDontCostALifeAndSpacesAreShown() {
        var g = HangmanGame(word: "ad hoc")
        g.guess("z"); g.guess("z")
        XCTAssertEqual(g.wrong, 1)
        XCTAssertTrue(g.shown(2)); XCTAssertFalse(g.isKey(2))
        for c in "adhoc" { g.guess(c) }
        XCTAssertTrue(g.won)
    }
}
