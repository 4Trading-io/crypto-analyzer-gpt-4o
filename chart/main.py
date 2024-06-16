import logging
from fetch_data import update_database
from analyze import main as analyze_main
import schedule
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_and_update(symbol, precision, interval):
    try:
        logging.info(f"Updating and analyzing {symbol} at interval {interval}")
        update_database(symbol, interval)
        analyze_main([(symbol, precision)], [interval])  # Pass the symbol and interval to analyze_main
    except Exception as e:
        logging.error(f"Error in update and analyze: {e}", exc_info=True)


def initial_analyze_and_update(symbols, presisions, intervals):
    try:
        logging.info("Starting initial data fetch and analysis")
        # Perform initial data load and analysis in the desired order
        for interval in intervals:
            for symbol, precision in zip(symbols, presisions):
                analyze_and_update(symbol, precision, interval)
    except Exception as e:
        logging.error(f"Error during initial data fetch and analysis: {e}", exc_info=True)

def schedule_tasks(symbols, precisions, intervals):
    try:
        logging.info("Scheduling periodic tasks")
        for interval in intervals:
            for symbol, precision in zip(symbols, precisions):
                logging.debug(f"Scheduling {interval} interval tasks for {symbol}")
                if interval == '15m':
                    schedule.every(1).days.at("04:00:00", 'UTC').do(analyze_and_update, symbol=symbol, precision=precision, interval=interval)
                    schedule.every(1).days.at("18:00:00", 'UTC').do(analyze_and_update, symbol=symbol, precision=precision, interval=interval)
                    # schedule.every(1).days.at("16:00:00", 'UTC').do(analyze_and_update, symbol=symbol, precision=precision, interval=interval)
                    # schedule.every(1).days.at("23:00:00", 'UTC').do(analyze_and_update, symbol=symbol, precision=precision, interval=interval)
                    # schedule.every(1).days.at("20:00:00", 'UTC').do(analyze_and_update, symbol=symbol, precision=precision, interval=interval)
                elif interval == '4h':
                    schedule.every(1).days.at("12:00:00", 'UTC').do(analyze_and_update, symbol=symbol, precision=precision, interval=interval)
                    # schedule.every(1).days.at("14:30:00", 'UTC').do(analyze_and_update, symbol=symbol, precision=precision, interval=interval)
                    # schedule.every(1).days.at("16:00:00", 'UTC').do(analyze_and_update, symbol=symbol, precision=precision, interval=interval)
                elif interval == '1d':
                    schedule.every(2).days.at("16:30:00", 'UTC').do(analyze_and_update, symbol=symbol, precision=precision, interval=interval)
    except Exception as e:
        logging.error(f"Error scheduling periodic tasks: {e}", exc_info=True)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)  

def main():
    try:
        logging.info("Starting main function")
        intervals = ['15m', '4h', '1d']  # Default intervals
        symbols = ['BTCUSDT', 'ETHUSDT']  # Example symbols
        precisions = [0, 0]
        logging.info("Setting up scheduled tasks")
        schedule_tasks(symbols, precisions, intervals)

        logging.info("Starting the scheduler")
        run_scheduler()
    except Exception as e:
        logging.error(f"Error in main function: {e}", exc_info=True)

if __name__ == "__main__":
    main()
