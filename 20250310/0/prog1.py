import cmd
import calendar
import shlex


class TextCalendar(cmd.Cmd):
    prompt = "cmd>> "
    tc = calendar.TextCalendar()

    def do_pryear(self, args):
        """Print the calendar for an entire year as returned by formatyear()."""
        self.tc.pryear(theyear=int(args))

    def do_prmonth(self, args):
        """Print a month’s calendar as returned by formatmonth()."""
        info = shlex.split(args)
        self.tc.prmonth(theyear=int(info[0]), themonth=eval(f"calendar.{info[1]}.value"))

    def complete_prmonth(self, text, line, begin, end):
        word = text.split()
        print(list((type(c.name), c.name) for c in calendar.Month))
        return [c for c in calendar.Month if c.name.startswith(*word)]

    def do_EOF(self, args):
        """Kill cmd when ^D appears"""
        return True


if __name__ == '__main__':
    TextCalendar().cmdloop()
