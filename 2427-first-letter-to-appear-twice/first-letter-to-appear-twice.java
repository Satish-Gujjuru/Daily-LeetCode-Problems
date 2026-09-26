class Solution {
    public char repeatedCharacter(String s) {
        ArrayList<Character> list = new ArrayList<>();
        for(int i=0;i<s.length();i++){
            if(list.contains(s.charAt(i)))
                return s.charAt(i);
            
            list.add(s.charAt(i));
        }
        return s.charAt(s.length()-1);
    }
}