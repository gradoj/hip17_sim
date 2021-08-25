import h3
import pandas as pd
import requests
from time import time
import json
import gencsv # generates hotspots.csv

density={0: {"N":  2, "density_tgt": 10000, "density_max": 10000},
        1: {"N":  2, "density_tgt": 10000, "density_max": 10000},
        2: {"N":  2, "density_tgt": 10000, "density_max": 10000},
        3: {"N":  2, "density_tgt": 10000, "density_max": 10000},
        4: {"N":  1, "density_tgt": 250, "density_max": 800},
        5: {"N":  1, "density_tgt": 100, "density_max": 400},
        6: {"N":  1, "density_tgt": 25, "density_max": 100},
        7: {"N":  2, "density_tgt": 5, "density_max": 20},
        8: {"N":  2, "density_tgt": 1, "density_max": 4},
        9: {"N":  2, "density_tgt": 1, "density_max": 2},
        10: {"N":  2, "density_tgt": 1, "density_max": 1}}


class scale_calculator:
    '''
        Helium hip17 scale calculator. takes a snapshot of all hotspots from the helium api and
        creates hotspots.csv. This scale calculator class calculates the hip17 scaling factor based
        off hotspots.csv and the density variable above so this can be used as a simulator to
        explore the effects of adjusting the variables on the scaling factor. 
    '''
    def __init__(self): # Initializing
        try:
            self.df=pd.read_csv("hotspots.csv")
        except FileNotFoundError:
            print('No hotspot.csv file. Getting latest from API...')
            gencsv.download_hotspots()
            self.df=pd.read_csv("hotspots.csv")

        # clean up the data remove spaces and brackets
        self.df.columns = self.df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')

        print("Total Hotspots: ", len(self.df))
        
        # want to drop the inactive hotspots so they are not used in density calculations
        # after 3600 blocks with no activity they are removed

        #print('block height minimum',self.df['height'].min())
        inactive_threshold=self.df['height'].max()-3600
        #print('inactive threshold',inactive_threshold)
        self.df_inactive = self.df[self.df.height < inactive_threshold]
        self.df = self.df[self.df.height >= inactive_threshold]

        self.df.dateadded = pd.to_datetime(self.df['dateadded'], format='%Y-%m-%d %H:%M:%S.%f')
        self.df.set_index(['address'],inplace=True)
        
        self.dups={}

        # get dataframe with number of duplicate hexes for each size
        # this is the same as number of hotspots in each hex
        self.dups[4] = self.df.pivot_table(index = ['hex4'], aggfunc ='size')
        self.dups[5] = self.df.pivot_table(index = ['hex5'], aggfunc ='size')
        self.dups[6] = self.df.pivot_table(index = ['hex6'], aggfunc ='size')
        self.dups[7] = self.df.pivot_table(index = ['hex7'], aggfunc ='size')
        self.dups[8] = self.df.pivot_table(index = ['hex8'], aggfunc ='size')
        self.dups[9] = self.df.pivot_table(index = ['hex9'], aggfunc ='size')
        self.dups[10] = self.df.pivot_table(index = ['hex10'], aggfunc ='size')

        self.scale_dict={}
        self.neighdict={}

    def get_neighbour_hotspots(self,h3hex):
        '''
            input: h3hex
            returns a pandas dataframe with hotspots in neighbouring hexes
        '''
        h3res=h3.h3_get_resolution(h3hex)
        hs_in_hex=pd.DataFrame()
        if h3res<4 or h3res>11:
            return hs_in_hex

        hs=[]
        neighbours = h3.hex_ring(h3hex,k=1)
        for neigh in neighbours:
            h3children=h3.h3_to_children(neigh)
            pdchildren=[]
            for h3child in h3children:
                pdchildren.append(self.df.loc[self.df['hex'+str(h3res+1)] == h3child])
            hs=hs+pdchildren
        hs_in_hex=pd.concat(hs)
        return hs_in_hex

    def get_hotspots(self,h3hex):
        '''
            input: h3hex
            returns a pandas dataframe with hotspots in the hex
        '''
        h3res=h3.h3_get_resolution(h3hex)
        hs_in_hex=pd.DataFrame()
        if h3res<4 or h3res>11:
            return hs_in_hex
        
        h3children=h3.h3_to_children(h3hex)
        pdchildren=[]
        for h3child in h3children:
            pdchildren.append(self.df.loc[self.df['hex'+str(h3res+1)] == h3child])

        hs_in_hex=pd.concat(pdchildren)
        return hs_in_hex
        
    def get_inactive_hotspots(self,h3hex):
        '''
            input: h3hex
            returns a pandas dataframe with inactive hotspots in that hex
            inactive hotspot is one with latest block at least 3600 behind 
        '''
        h3res=h3.h3_get_resolution(h3hex)
        hs_in_hex=pd.DataFrame()
        if h3res<4 or h3res>11:
            return hs_in_hex
        
        h3children=h3.h3_to_children(h3hex)
        pdchildren=[]
        for h3child in h3children:
            pdchildren.append(self.df_inactive.loc[self.df_inactive['hex'+str(h3res+1)] == h3child])

        hs_in_hex=pd.concat(pdchildren)
        return hs_in_hex
        
    def get_num_neighbours(self,h3hex):
        # pass in hex and get number of occupied neighbour hexes
        neighbours = h3.hex_ring(h3hex,k=1)
        h3res=h3.h3_get_resolution(h3hex)
        num_neighbours_target=0
        for h in neighbours:
            try:
                if self.dups[h3res][h]>=density[h3res]['density_tgt']:
                #if self.sum_hotspots_re(h)>=density[h3res]['density_tgt']:

                    num_neighbours_target+=1
            except KeyError:
                # no hotspots in hex neighbour
                continue
        return num_neighbours_target
    
    def get_neighbours(self,h3hex):
        '''
            input: h3hex of interest
            returns a list of dictionaries of neighbouring hotspots
            neighdict[n]={'occupied':True,'num_hs':33,'target_density':25}
        '''
        h3res=h3.h3_get_resolution(h3hex)
        if h3res<4 or h3res>10:
            return {}

        neighbours = h3.hex_ring(h3hex,k=1)
        num_neighbours_target=0
        neighdict={}
        for h in neighbours:
            neigh_total=self._sum_hotspots_neighbours_re(h)
            if neigh_total>=density[h3res]['density_tgt']:
                num_neighbours_target+=1
                neighdict[h]={'occupied':True,'num_hs':neigh_total,'target_density':density[h3res]['density_tgt']}
            else:
                neighdict[h]={'occupied':False,'num_hs':neigh_total,'target_density':density[h3res]['density_tgt']}
        return neighdict

    def _get_num_hotspots(self,h3hex):
        ''' helper function that returns the total number of hotspots in a hex
            input: h3hex
            returns total number of active hotspots in a hex
        '''
        h3res=h3.h3_get_resolution(h3hex)
        try:
            num=self.dups[h3res][h3hex]
        except KeyError:
            num=0
        return num



    def _sum_hotspots_neighbours_re(self,h3hex):
        ''' recursive function to add up hotspots in a neighbouring hex
            this is a simplified version of sum_hotspots_re used when
            determining whether the neighbour is occupied or not
        '''
      
        h3res=h3.h3_get_resolution(h3hex)

        if h3res == 10:
            clipped=self.get_num_clipped_hotspots(h3hex)
 
        else:
            # check if there are any hotspots
            try:
                num_hs=self.dups[h3res][h3hex]
            except KeyError:
                num_hs=0
            if num_hs:
                h3children=h3.h3_to_children(h3hex)
                total_hotspots=0
                for child in h3children:
                    total_hotspots+=self._sum_hotspots_neighbours_re(child)
            else:   # there are not so don't need to look at children
                total_hotspots=0  
 
            clipped=total_hotspots
            
        return clipped
 
    
    def _sum_hotspots_re(self,h3hex,h3fam=[0,]):
        '''
            recursive function to add up hotspots in hex
            get hex children and keep getting children until down to r10 where hip17 stops.
            Add all hotspots up in r10 and record clipped value. Then add all clipped
            values in the r9,r8...r4. Calculate r4 scaling by target_density/clipped_number_hotspots

            input: h3hex and list of hexes in h3 family R4-R10
            returns clipped number of hotspots for this hex
        '''    
        
        h3res=h3.h3_get_resolution(h3hex)

        if h3res == 10:
            clipped=self.get_num_clipped_hotspots(h3hex)
            try:
                total_hotspots=self.dups[h3res][h3hex]
            except KeyError:
                total_hotspots=0
            densitytarget=self.get_density_max(h3hex)

        else:
            # check if there are any hotspots
            try:
                num_hs=self.dups[h3res][h3hex]
            except KeyError:
                num_hs=0
                
            if num_hs:
                h3children=h3.h3_to_children(h3hex)
                total_hotspots=0
                for child in h3children:
                    total_hotspots+=self._sum_hotspots_re(child,h3fam)
            else:   # there are not so don't need to look at children
                total_hotspots=0
                
            densitytarget=self.get_density_max(h3hex)
            clipped=total_hotspots
            
        # check if this hex is in the family so we can record it
        if h3hex in h3fam:
            if total_hotspots<densitytarget:
                scale=1.0
            else:
                scale=densitytarget/total_hotspots

            neighbours=self.get_neighbours(h3hex)
            ncount=0
            for key in neighbours:
                if neighbours[key]['occupied']:
                    ncount+=1
            self.scale_dict[h3res]={'num_hs':total_hotspots, 'h3res':h3res,'h3hex':h3hex,'target_density':densitytarget,'clipped_num_hs':clipped,
                             'occupied_neighbours':ncount,'scale':scale}

            #if clipped > densitytarget:
            #    clipped=densitytarget

        return clipped

    
    def get_density_max(self,h3hex):
        ''' gets the max density of hotspots in a hex
            input: h3hex
            output: maximum target density of a hex. Uses number of occupied neighbours and density variable at top of this file
        '''
        r=h3.h3_get_resolution(h3hex)
        
        neighbours = self.get_neighbours(h3hex)
        ncount=0
        for key in neighbours:
            if neighbours[key]['occupied']:
                ncount+=1
        try:
            target_density=(int(ncount/density[r]['N']) + 1) * density[r]['density_tgt']
            if target_density > density[r]['density_max']:
                target_density = density[r]['density_max']
        except:
            raise Exception()
        
        return target_density
    
    def get_num_clipped_hotspots(self,h3hex):
        ''' gets the clipped value for input hex
            returns min(target_density,number_of_hotspots) 
        '''
        r=h3.h3_get_resolution(h3hex)
        clipped_num_hs=self._get_num_hotspots(h3hex)
        num_neighbours = self.get_num_neighbours(h3hex)

        target_density=(int(num_neighbours/density[r]['N']) + 1) * density[r]['density_tgt']
        if target_density > density[r]['density_max']:
            target_density = density[r]['density_max']
        
        if clipped_num_hs > target_density:
            # more hs in this hex than the target. clip it
            clipped_num_hs=target_density

        return clipped_num_hs


    # pass in hex and this function returns the scaling factor
    # need to get h3hex parent up to res 4(where hip 17 stops).
    # and then sum up all r4 childrens number of
    # clipped hotspots to get r4 scaling factor. But this needs to happen
    # all the way down to r10. The annoying part is to get
    # r10 scaling factor you need to get r4,5,6,7,8,9 and multiply them all. To
    # get r4 scaling factor means adding up all hotspots(clipped value from density variable)
    # in every r10 all the way up.
    #           r4
    #         r5  r5
    #       r6  r6  r6
    #      ... ... ...
    # To calculate r4 scaling factor:
    # 1. get children all the way down to r10
    # 2. sum up all clipped values of each r10 hex
    # 3. take those and pass them to sum up all clipped values of each r9,8,7,6,5 all the way up
    # 4. calculate r4 scaling factor=density_tgt/num_clipped_hs
    def get_scale(self,h3hex):
        h3fam=[]
        num_hs=0
        res=h3.h3_get_resolution(h3hex)

        if (res<4 or res>10 ):
            return 0
        
        for r in range(res,3,-1):
            h3fam.append(h3hex)
            if r>4: # r4 is the largest hip17 currently uses so stop here
                h3hex=h3.h3_to_parent(h3hex)
            
        #print('h3fam',h3fam)

        if (res>3 or res<11 ): # scale ends at 4 so don't call for any physically larger hexes
            num_hs=self._sum_hotspots_re(h3hex,h3fam)

        return self.scale_dict[res]['scale']
 
    
    def __del__(self): # Calling destructor
        pass
        #print("Destroy Class") 

if __name__ == "__main__":

    sc=scale_calculator()

    start = time()
    print('Scale for 8412ccdffffffff',sc.get_scale('8412ccdffffffff'))
    print(sc.scale_dict)
    end = time()
    print(f'It took {end - start} seconds')

    start = time()
    print('Scale for 8a12ccd5091ffff',sc.get_scale('8a12ccd5091ffff'))
    print(sc.scale_dict)
    end = time()
    print(f'It took {end - start} seconds')



