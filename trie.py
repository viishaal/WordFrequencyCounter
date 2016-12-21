class TrieNode(object):

    def __init__(self):
        """
        Initialize your data structure here.
        """
        self.child = [None] * 26
        self.is_leaf = False
        

class Trie(object):

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        """
        Inserts a word into the trie.
        :type word: str
        :rtype: void
        """
        if len(word) == 0:
            return

        start = ord('a')
        ptr = self.root
        for i, ch in enumerate(word):
            idx = ord(ch) - start
            # traverse
            if ptr.child[idx] == None:
                # insert the rest in trie
                for ch in word[i:]:
                    idx = ord(ch) - start
                    ptr.child[idx] = TrieNode()
                    ptr = ptr.child[idx]
                break
            else:
                ptr = ptr.child[idx]

        ptr.is_leaf = True
            
            

    def search(self, word):
        """
        Returns if the word is in the trie.
        :type word: str
        :rtype: bool
        """
        start = ord('a')
        ptr = self.root
        for i, ch in enumerate(word):
            idx = ord(ch) - start
            if ptr.child[idx] == None:
                return False
            else:
                ptr = ptr.child[idx]
        
        if not ptr.is_leaf:
            return False
        else:
            return True

        

    def startsWith(self, prefix):
        """
        Returns if there is any word in the trie
        that starts with the given prefix.
        :type prefix: str
        :rtype: bool
        """        
        start = ord('a')
        ptr = self.root
        for i, ch in enumerate(prefix):
            idx = ord(ch) - start
            if ptr.child[idx] == None:
                return False
            else:
                ptr = ptr.child[idx]
        
        return True

        

# Your Trie object will be instantiated and called as such:
# trie = Trie()
# trie.insert("somestring")
# trie.search("key")