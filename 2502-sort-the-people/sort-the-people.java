class Solution {
    public String[] sortPeople(String[] names, int[] heights) {
        for(int i=0;i<names.length;i++){
            int min = i;

            for(int j=i+1;j<names.length;j++){
                if(heights[j] > heights[min])
                    min = j;
            }
            int temp1 = heights[min];
            String temp2 = names[min];
            heights[min] = heights[i];
            names[min] = names[i];
            heights[i] = temp1;
            names[i] = temp2;
        }
        return names;
    }
}