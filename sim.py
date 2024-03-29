'''
        Queue Simulation script
'''

import simpy
import random
import pandas as pd


#STATISTICS
counter_balk = 0
counter_arrive = 0
counter_served = 0
counter_in_system = 0

collect_serv_time = list()
collect_arrival_time = list()
collect_wait_time = list()

c = ['time', 'state_num']
state_log = pd.DataFrame(columns=c)
arrive_log = pd.DataFrame(columns=c)
depart_log = pd.DataFrame(columns=c)




def source(env, _lambda, _mu, _alpha):
        ''' 
        Generates new clients according to Pois distribution with parameter _lambda.
        Generate time between arrivals comming as X~Exp(_lambda)        
        E.g. 3 arrivals/per hour means that arrival occurs in mean in 20 min(or 1/3 hour). So time between arrivals can be described as Exp(3)
        
        '''     
        i = 0
        while True:
                i += 1
                name = 'customer' + str(i)        
                c = customer(env, _mu, _alpha, name)
                env.process(c) # add process to go
                arrive_time = random.expovariate(_lambda)
                collect_arrival_time.append(arrive_time)
                yield env.timeout(arrive_time)


def customer(env, _mu, _alpha, name):
        '''
        Customer arrives, waits for service or goes away
        '''
        global counter_served, counter_arrive, counter_balk, counter_in_system, state_log, arrive_log, depart_log,\
                collect_serv_time, collect_arrival_time, collect_wait_time
        
        arrive = env.now
        if random.random() > _alpha:
                counter_balk +=1
                return
        else:   
                counter_arrive +=1
                counter_in_system +=1
                state_log = state_log.append( {'time' : env.now , 'state_num': counter_in_system}, ignore_index=True )
                arrive_log = arrive_log.append({'time' : env.now , 'state_num': counter_arrive}, ignore_index=True)

        with serv.request() as req:

                yield req #wait 
                wait = env.now - arrive
                collect_wait_time.append(wait)
                serve_time = random.expovariate(_mu)
                collect_serv_time.append(serve_time)         
                yield env.timeout(serve_time)

                counter_served += 1
                counter_in_system -= 1
                state_log = state_log.append( {'time' : env.now , 'state_num': counter_in_system}, ignore_index=True )
                depart_log = depart_log.append({'time' : env.now , 'state_num': counter_served}, ignore_index=True)
                



def simulate(_lambda, _mu, _alpha, until = 50):
        global counter_served, counter_arrive, counter_balk, counter_in_system, state_log, arrive_log,\
                 depart_log, collect_serv_time, collect_arrival_time, collect_wait_time

        counter_balk = 0
        counter_arrive = 0
        counter_served = 0
        counter_in_system = 0

        collect_serv_time = list()
        collect_arrival_time = list()
        collect_wait_time = list()

        c = ['time', 'state_num']
        state_log = pd.DataFrame(columns=c)
        arrive_log = pd.DataFrame(columns=c)
        depart_log = pd.DataFrame(columns=c)

        run(_lambda, _mu, _alpha, until)

        stat = {
                'state_log' : state_log, 
                'arrive_log' : arrive_log,
                'depart_log' : depart_log,
                'served_num' : counter_served,
                'arrived_num' :  counter_arrive,
                'bulk_num' :  counter_balk,
                'mean_wait_time' : sum(collect_wait_time ) / len(collect_wait_time),
                'mean_serv_time' : sum(collect_serv_time ) / len(collect_serv_time),
                'mean_arrive_time' : sum(collect_arrival_time ) / len(collect_arrival_time)
        }

        print("Количество отвергнутых требований: {}".format(counter_balk))
        print("Количество прибывших требований: {}".format(counter_arrive))
        print("Количество покинувших требований: {}".format(counter_served))
        print('Среднее время обслуживания: %7.4f'% (sum(collect_serv_time ) /len(collect_serv_time)))
        print('Среднее время прибытия: %7.4f'%( sum(collect_arrival_time) / len(collect_arrival_time)))
        print('Среднее время ожидания: %7.4f'%(sum(collect_wait_time) / len(collect_wait_time)))
        return stat



def run(_lambda, _mu, _alpha, until):        
        global env, serv

        env = simpy.Environment()
        serv = simpy.Resource(env, capacity=1)
        env.process(source( env,  _lambda, _mu, _alpha ))
        env.run(until= until)


if __name__ == '__main__':

        _lambda = 3 # e.g. 3 person per hour
        _mu = 1 # e.g. _mu = 3 if mean serving time is 20 min
        _alpha = 0.7 # stay in system with probability _alpha

        simulate(_lambda, _mu, _alpha, until = 10000)








