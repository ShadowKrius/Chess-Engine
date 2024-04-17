# This class is responsible for storing all the information about the current state of the chess game
# It will also be responsible for determining the valid moves at the current state
# It will also keep a move log
import copy

class GameState():
    def __init__(self):
        # board is an 8x8 2-dimensional list, each element of the list has 2 characters
        # the first character represents the color of the piece, "b" or "w"
        # the second character represents the type of the piece, "K", "Q", "B", "R", "N" or "P"
        # the string "--" represents an empty space with no piece
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        self.moveFunctions = {"P": self.getPawnMoves, "R": self.getRookMoves, "K": self.getKingMoves, 
                              "Q": self.getQueenMoves, "B": self.getBishopMoves, "N": self.getKnightMoves}
        
        self.whiteToMove = True
        self.moveLog = []
        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.inCheck = False
        self.pins = []
        self.checks = []
        self.checkmate = False
        self.stalemate = False
        self.enpassantPossible = () # coordinates of the square where an en passant capture is possible
        self.enpassantPossibleLog = [self.enpassantPossible]
        self.currentCastleRight = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(self.currentCastleRight.wks, self.currentCastleRight.bks, self.currentCastleRight.wqs, self.currentCastleRight.bqs)]
        
    # takes a move as a parameter and executes it (will not work for castling, en-passant and pawn promotion)
    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move) # log the move so we can undo it later
        self.whiteToMove = not self.whiteToMove # switch turns
        # update the king's location if moved
        if move.pieceMoved == "wK":
            self.whiteKingLocation = (move.endRow, move.endCol)
        if move.pieceMoved == "bK":
            self.blackKingLocation = (move.endRow, move.endCol)
        # pawn promotion, auto-queen
        if move.isPawnPromotion:
            # promotedPiece = input("Promote to Q, R, B or N: ") # need to make this part of the ui later
            promotedPiece = "Q"
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + promotedPiece
            
        # enpassant move
        if move.isEnpassantMove:
            self.board[move.startRow][move.endCol] = "--" # capturing the pawn
        # update isEnpassantPossible variable
        if move.pieceMoved[1] == "P" and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = ((move.startRow + move.endRow)//2, move.endCol)
        else:
            self.enpassantPossible = ()
        self.enpassantPossibleLog.append(self.enpassantPossible)
            
        # castle move
        if move.isCastleMove:
            if move.endCol - move.startCol == 2: # kingside castle move
                self.board[move.endRow][move.endCol-1] = self.board[move.endRow][move.endCol+1] # moves the rook
                self.board[move.endRow][move.endCol+1] = "--" # erases the old rook
            else: # queenside castle move
                self.board[move.endRow][move.endCol+1] = self.board[move.endRow][move.endCol-2] # moves the rook
                self.board[move.endRow][move.endCol-2] = "--" # erases the old rook
        # update castling rights - whenever it is a king or a rook move
        self.updateCastleRights(move)
        self.castleRightsLog.append(CastleRights(self.currentCastleRight.wks, self.currentCastleRight.bks, self.currentCastleRight.wqs, self.currentCastleRight.bqs))
 
    # undo the last move made
    def undoMove(self):
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove # switch turns back
            # update the king's position if needed
            if move.pieceMoved == "wK":
                self.whiteKingLocation = (move.startRow, move.startCol)
            if move.pieceMoved == "bK":
                self.blackKingLocation = (move.startRow, move.startCol)
            # undo en passant move
            if move.isEnpassantMove:
                self.board[move.endRow][move.endCol] = "--"
                self.board[move.startRow][move.endCol] = move.pieceCaptured
            self.enpassantPossibleLog.pop()
            self.enpassantPossible = self.enpassantPossibleLog[-1]
            
            # undo castling rights
            self.castleRightsLog.pop() # we get rid of the new castling rights from the move we are undoing
            castle_rights = copy.deepcopy(self.castleRightsLog[-1])
            self.currentCastleRight = castle_rights # set the current castle rights to the last one in the list
            # undo the castle move
            if move.isCastleMove:
                if move.endCol - move.startCol == 2: # kingside
                    self.board[move.endRow][move.endCol+1] = self.board[move.endRow][move.endCol-1]
                    self.board[move.endRow][move.endCol-1] = "--"
                else:
                    self.board[move.endRow][move.endCol-2] = self.board[move.endRow][move.endCol+1]
                    self.board[move.endRow][move.endCol+1] = "--"
        self.checkmate = False
        self.stalemate = False
        
    # update the castle rights given the move        
    def updateCastleRights(self, move):
        if move.pieceMoved == "wK":
            self.currentCastleRight.wks = False
            self.currentCastleRight.wqs = False
        elif move.pieceMoved == "bK":
            self.currentCastleRight.bks = False
            self.currentCastleRight.bqs = False
        elif move.pieceMoved == "wR":
            if move.startRow == 7:
                if move.startCol == 0: # left rook
                    self.currentCastleRight.wqs = False
                elif move.startCol == 7: # right rook
                    self.currentCastleRight.wks = False
        elif move.pieceMoved == "bR":
            if move.startRow == 0:
                if move.startCol == 0: # left rook
                    self.currentCastleRight.bqs = False
                elif move.startCol == 7: # right rook
                    self.currentCastleRight.bks = False
                    
        # if a rook is captured
        if move.pieceCaptured == "wR":
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastleRight.wqs = False
                elif move.endCol == 7:
                    self.currentCastleRight.wks = False
        elif move.pieceCaptured == "bR":
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastleRight.bqs = False
                elif move.endCol == 7:
                    self.currentCastleRight.bks = False
                
    # returns all moves considering checks
    def getValidMoves(self):
        moves = []
        if self.whiteToMove:
            kingRow = self.whiteKingLocation[0]
            kingCol = self.whiteKingLocation[1]
        else:
            kingRow = self.blackKingLocation[0]
            kingCol = self.blackKingLocation[1]
        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks(kingRow, kingCol)
        if self.inCheck:
            if len(self.checks) == 1: # only 1 check, either block check or move king
                moves = self.getAllPossibleMoves()
                # to block a check you must move a piece into one of the squares between the enemy piece and the king
                check = self.checks[0]
                checkRow = check[0]
                checkCol = check[1]
                pieceChecking = self.board[checkRow][checkCol] # enemy piece causing the check
                validSquares = [] # squares that piece can move to 
                if pieceChecking[1] == "N": # if knight we must capture the knight or move the king
                    validSquares = [(checkRow, checkCol)]
                else:
                    for i in range(1, 8):
                        validSquare = (kingRow + check[2] * i, kingCol + check[3] * i) # check [2] and [3] are the check directions
                        validSquares.append(validSquare)
                        if validSquare[0] == checkRow and validSquare[1] == checkCol: # once you get to the piece end checks
                            break
                # get rid of any moves that don't block check or move king
                for i in range(len(moves)-1, -1, -1): # go through backwards when you are removing from a list as iterating
                    if moves[i].pieceMoved[1] != "K": # move doesn't move king so it must block or capture
                        if not (moves[i].endRow, moves[i].endCol) in validSquares:
                            moves.remove(moves[i])
            else: # double check, king has to move
                self.getKingMoves(kingRow, kingCol, moves)
            if moves == []:
                self.checkmate = True
        else: # not in check so all moves are fine
            moves = self.getAllPossibleMoves()
            if moves == []:
                self.stalemate = True
        if self.whiteToMove:
            self.getCastleMoves(self.whiteKingLocation[0], self.whiteKingLocation[1], moves)
        else:
            self.getCastleMoves(self.blackKingLocation[0], self.blackKingLocation[1], moves)
        return moves
                                        
    def checkForPinsAndChecks(self, r, c):
        pins = [] # squares where the allied pinned pieces are and the direction they are pinned from
        checks = [] # squares where the enemy is applying a check
        inCheck = False
        if self.whiteToMove:
            enemyColor = "b"
            allyColor = "w"
        else:
            enemyColor = "w"
            allyColor = "b"
        startRow = r
        startCol = c
        # check outward from king for pins and checks, keep track of pins
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            possiblePin = () # reset possible pins
            for i in range(1, 8):
                endRow = startRow + d[0] * i
                endCol = startCol + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyColor and endPiece[1] != "K": # we add the second part to solve the problem of the phantom king
                        if possiblePin == (): # 1st allied piece could be pinned
                            possiblePin = (endRow, endCol, d[0], d[1])
                        else: # 2nd allied piece, so no pin or check possible in this direction
                            break
                    elif endPiece[0] == enemyColor:
                        type = endPiece[1]
                        if (0 <= j <= 3 and type == "R") or (4 <= j <= 7 and type == "B") or \
                            (i == 1 and type == "P" and ((enemyColor == "w" and 6 <= j <= 7) or (enemyColor == "b" and 4 <= j <= 5))) or \
                            (type == "Q") or (i == 1 and type == "K"):
                            if possiblePin == (): # no piece blocking so check
                                inCheck = True
                                checks.append((endRow, endCol, d[0], d[1]))
                                break
                            else: # piece blocking so pin
                                pins.append(possiblePin)
                                break
                        else: # enemy piece not applying check
                            break
                else: # off board
                    break
        # check for knight moves
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for m in knightMoves:
            endRow = startRow + m[0]
            endCol = startCol + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] == enemyColor and endPiece[1] == "N": # enemy knight attacking the king
                    inCheck = True
                    checks.append((endRow, endCol, m[0], m[1]))
        return inCheck, pins, checks
        
    # determine if the enemy can attack the square (r, c)
    def squareUnderAttack(self, r, c):
        self.whiteToMove = not self.whiteToMove
        oppMoves = self.getAllPossibleMoves() # generate all opponent's moves
        self.whiteToMove = not self.whiteToMove # switch turns back
        for move in oppMoves:
            if move.endRow == r and move.endCol == c: # square is under attack
                return True
        return False
        
    # returns all moves without considering checks
    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == "w" and self.whiteToMove) or (turn == "b" and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves) # calls the appropriate move function based on the piece type
        return moves
                    
    # get all the pawn moves for the pawn located at row, col and add these moves to the list
    def getPawnMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
            
        if self.whiteToMove:
            moveAmount = -1
            startRow = 6
            enemyColor = "b"
            kingRow, kingCol = self.whiteKingLocation
        else:
            moveAmount = 1
            startRow = 1
            enemyColor = "w"
            kingRow, kingCol = self.blackKingLocation
            
        if self.board[r+moveAmount][c] == "--":
            if not piecePinned or pinDirection == (moveAmount, 0):
                moves.append(Move((r, c), (r+moveAmount, c), self.board))
                if r == startRow and self.board[r+2*moveAmount][c] == "--": # 2 square pawn advance
                    moves.append(Move((r, c), (r+2*moveAmount, c), self.board))
        if c-1 >= 0: # captures to the left
            if not piecePinned or pinDirection == (moveAmount, -1):
                if self.board[r+moveAmount][c-1][0] == enemyColor:
                    moves.append(Move((r, c), (r+moveAmount, c-1), self.board))
                if (r+moveAmount, c-1) == self.enpassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c: # king is left of the pawn
                            # inside between king and pawn; outside between pawn and border
                            insideRange = range(kingCol+1, c-1)
                            outsideRange = range(c+1, 8)
                        else: # king is right of the pawn
                            insideRange = range(kingCol-1, c, -1)
                            outsideRange = range(c-2, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != "--": # some other piece beside enpassant pawn blocks
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == enemyColor and (square[1] == "R" or square[1] == "Q"): # attacking piece exists
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r+moveAmount, c-1), self.board, isEnpassantMove=True))
        if c+1 <= 7: # captures to the right
            if not piecePinned or pinDirection == (moveAmount, 1):
                if self.board[r+moveAmount][c+1][0] == enemyColor: # enemy piece exists to capture
                    moves.append(Move((r, c), (r+moveAmount, c+1), self.board))
                elif (r+moveAmount, c+1) == self.enpassantPossible:
                    attackingPiece = blockingPiece = False
                    if kingRow == r:
                        if kingCol < c: # king is left of the pawn
                            # inside between king and pawn; outside between pawn and border
                            insideRange = range(kingCol+1, c)
                            outsideRange = range(c+2, 8)
                        else: # king is right of the pawn
                            insideRange = range(kingCol-1, c+1, -1)
                            outsideRange = range(c-1, -1, -1)
                        for i in insideRange:
                            if self.board[r][i] != "--": # some other piece beside enpassant pawn blocks
                                blockingPiece = True
                        for i in outsideRange:
                            square = self.board[r][i]
                            if square[0] == enemyColor and (square[1] == "R" or square[1] == "Q"): # attacking piece exists
                                attackingPiece = True
                            elif square != "--":
                                blockingPiece = True
                    if not attackingPiece or blockingPiece:
                        moves.append(Move((r, c), (r+moveAmount, c+1), self.board, isEnpassantMove=True))
    
    # get all the rook moves for the rook located at row, col and add these moves to the list
    def getRookMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != "Q": # can't remove queen from pin on rook moves, only remove it on bishop moves
                    self.pins.remove(self.pins[i])
                break
        
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1)) # up, left, down, right
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8): # rook can move a maximum of 7 squares in each direction
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--": # empty valid square
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor: # enemy piece valid
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else: # friendly piece invalid
                            break
                else: # off the board
                    break
                
    # get all the Bishop moves for the Bishop located at row, col and add these moves to the list
    def getBishopMoves(self, r, c, moves):
        piecePinned = False
        pinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                pinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1)) # 4 diagonals
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8): # bishop can move a maximum of 7 squares in each diagonal
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    if not piecePinned or pinDirection == d or pinDirection == (-d[0], -d[1]):
                        endPiece = self.board[endRow][endCol]
                        if endPiece == "--": # empty valid square
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                        elif endPiece[0] == enemyColor: # enemy piece valid
                            moves.append(Move((r, c), (endRow, endCol), self.board))
                            break
                        else: # friendly piece invalid
                            break
                else: # off the board
                    break
    
    # get all the Knight moves for the Knight located at row, col and add these moves to the list
    def getKnightMoves(self, r, c, moves):
        piecePinned = False
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                piecePinned = True
                self.pins.remove(self.pins[i])
                break
        
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)) # 8 knight L moves
        sameColor = "w" if self.whiteToMove else "b"
        for d in knightMoves:
            endRow = r + d[0]
            endCol = c + d[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                if not piecePinned:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != sameColor: # not an ally piece (empty square or enemy piece)
                        moves.append(Move((r, c), (endRow, endCol), self.board))
    
    # get all the Queen moves for the Queen located at row, col and add these moves to the list
    def getQueenMoves(self, r, c, moves):
        self.getBishopMoves(r, c, moves)
        self.getRookMoves(r, c, moves)
    
    # get all the King moves for the King located at row, col and add these moves to the list
    def getKingMoves(self, r, c, moves):
        rowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        colMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        sameColor = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + rowMoves[i]
            endCol = c + colMoves[i]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != sameColor: # not an ally piece (empty square or enemy piece)
                    # place king on end square and check for checks
                    if sameColor == "w":
                        self.whiteKingLocation = (endRow, endCol)
                    else:
                        self.blackKingLocation = (endRow, endCol)
                    inCheck, pins, checks = self.checkForPinsAndChecks(endRow, endCol)
                    if not inCheck:
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                    # place king back on the original square
                    if sameColor == "w":
                        self.whiteKingLocation = (r, c)
                    else:
                        self.blackKingLocation = (r, c)
        
    # generate all valid castle moves for the king at (r, c) and add them to the list of valid moves
    def getCastleMoves(self, r, c, moves):
        inCheck, pins, checks = self.checkForPinsAndChecks(r, c)
        if inCheck:
            return
        if (self.whiteToMove and self.currentCastleRight.wks) or (not self.whiteToMove and self.currentCastleRight.bks):
            self.getKingsideCastleMoves(r, c, moves)
        if (self.whiteToMove and self.currentCastleRight.wqs) or (not self.whiteToMove and self.currentCastleRight.bqs):
            self.getQueensideCastleMoves(r, c, moves)
            
    def getKingsideCastleMoves(self, r, c, moves):
        if self.board[r][c+1] == "--" and self.board[r][c+2] == "--":
            if not self.squareUnderAttack(r, c+1) and not self.squareUnderAttack(r, c+2):
                moves.append(Move((r, c), (r, c+2), self.board, isCastleMove=True))
        
    def getQueensideCastleMoves(self, r, c, moves):
        if self.board[r][c-1] == "--" and self.board[r][c-2] == "--" and self.board[r][c-3] == "--":
            if not self.squareUnderAttack(r, c-1) and not self.squareUnderAttack(r, c-2):
                moves.append(Move((r, c), (r, c-2), self.board, isCastleMove=True))
                        
class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs
        
class Move():
    # maps keys to values
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()} # reverses the dictionary
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()} # reverses the dictionary
    
    def __init__(self, startSq, endSq, board, isEnpassantMove=False, isCastleMove=False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        # pawn promotion
        self.isPawnPromotion = ((self.pieceMoved == "wP" and self.endRow == 0) or (self.pieceMoved == "bP" and self.endRow == 7))
        # en passant
        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove:
            self.pieceCaptured = "wP" if self.pieceMoved == "bP" else "bP"
        # capture move
        self.isCapture = self.pieceCaptured != "--"
        # castle move
        self.isCastleMove = isCastleMove
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol
        
    # overriding the equals method
    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False
            
    def getChessNotation(self):
        # TODO: add more logic to write real chess notation
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)
        
    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]
    
    # overriding the str() function
    def __str__(self):
        # castle move
        if self.isCastleMove:
            # "O-O": king side castle
            # "O-O-O": queen side castle
            return "O-O" if self.endCol == 6 else "O-O-O"
        
        endSquare = self.getRankFile(self.endRow, self.endCol)
        # pawn moves
        if self.pieceMoved[1] == "P":
            if self.isCapture:
                return self.colsToFiles[self.startCol] + "x" + endSquare
            else:
                return endSquare
            # TODO: pawn promotion
        
        # two of the same type of piece moving to a square, Nbd2 if both knights can move to d2
        
        # also adding + for a check move, and adding # for a checkmate move
        
        # piece moves
        moveString = self.pieceMoved[1]
        if self.isCapture:
            moveString += "x"
        return moveString + endSquare