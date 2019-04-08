from flask import Flask, jsonify, request
import time
import logging as log

log.getLogger().setLevel(log.INFO)
app = Flask(__name__)


HOSTS_COUNT = 10
# Generate hosts pool
IP_POOL = [{'ip': '192.168.0.' + str(host), 'task_end_time': 0} for host in range(1, HOSTS_COUNT + 1)]

log.info('Pool generated: %s' % IP_POOL)

def get_slaves(amount, duration):
    # store current time in seconds
    now = int(time.time())
    # sort hosts pool, None first, then lows to highest by time
    sorted_pool = sorted(
        IP_POOL, key=lambda k: k['task_end_time'])

    log.info('sorted_pool -> \n%s' % sorted_pool)

    # in sorted_pool, if item on index 'amount' is 'free' (its task ended), 
    # then items from index 0 to 'amount' are free as well.  note: array starts from index 0
    is_free = True if now > sorted_pool[amount - 1]['task_end_time'] else False

    log.info('Do we have any free hosts? %s' % is_free)

    if is_free:
        # we can now allocate those hosts
        allocated_hosts = [host for host in sorted_pool[0:amount]]
        log.info('Allocating hosts: %s' % allocated_hosts)

        for host in allocated_hosts:
            # set tasks end time
            host['task_end_time'] = now + duration
            log.info('Host %s was allocated to %s' % (host['ip'], host['task_end_time']))
            # update original pool
            # find the index of that host
            index = [host['ip'] for host in IP_POOL].index(host['ip'])
            IP_POOL[index]['task_end_time'] = host['task_end_time']
        # return only the host

        log.info('Updated Pool: %s' % IP_POOL)
        return [host['ip'] for host in allocated_hosts], None

    # if it's not free, we need to wait task on index 'amount' to be free
    # by that time, hosts on indexes 0 to 'amount' - 1 will be free as well
    else:
        come_back = sorted_pool[amount - 1]['task_end_time'] - now
        return None, come_back

@app.route("/get_slaves", methods=['GET'])
def get_slaves_api():
    args = request.args
    # get url params
    try:
        amount = args.get('amount', type=int)
        duration = args.get('duration', type=int)

        log.info('recived params -> amount: %s, duration: %s' % (amount, duration))
        # validate
        if duration < 1 or amount < 1 or amount > HOSTS_COUNT:
            return jsonify(error='bad params')

    except Exception as e:
        print(e)
        return ValueError('bad params')

    slaves, come_back = get_slaves(amount, duration)
    if come_back:
        return jsonify(slaves=[], come_back=come_back)
        
    return jsonify(slaves=slaves)


if __name__ == '__main__':
      app.run(host='0.0.0.0', port=8080)
