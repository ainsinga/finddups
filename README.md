README.md for finddups1.py (python3)

Copyright 2024 Aron K. Insinga

>Licensed under the Apache License, Version 2.0 (the "License");
>you may not use this file except in compliance with the License.
>You may obtain a copy of the License at
>
>    http://www.apache.org/licenses/LICENSE-2.0
>
>Unless required by applicable law or agreed to in writing, software
>distributed under the License is distributed on an "AS IS" BASIS,
>WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
>See the License for the specific language governing permissions and
>limitations under the License.

>This software contains a copy of an ADIF parser by Andreas Kraeger, DJ3EI.
>The only changes to it were to add parens after the argument to print
>to fix a python2-python3 incompatibility.  See
>/adif-io/adif_io-0.0.3/adif_io/\_\_init\_\_.py

finddups1.py is a PROTOTYPE program for finding DUPLICATE, UNCONFIRMED
entries in an ADIF file.  If one of the copies is confirmed, that is a
"keeper"!  (Not that you can do anything to the duplicate [or
incorrect] data in the ARRL LotW database.)  This is completely
unrelated to "dups" as in "dup sheets" or scoring for contests.

 * This program has a bunch of TODO and FIXME comments in it.
 * This program is not a finished product; do not rely on its correctness.
 * This program needs to be modified for your exact needs.
 * This program does not affect any databases, it just prints some output.

THE REAL PROBLEM WAS A DIFFERENT NUMBER OF DIGITS IN THE EXPORTED
FREQUENCY.  Some web sites or log programs let you change the number
of decimal places to use when exporting ADIF.  But LotW will see
e.g. 13.729 and 13.700 as different QOSs!  To put it another way, I
should have known to NEVER EXPORT FROM CLUBLOG OR LET IT UPLOAD TO LOTW.

See the comments in finddups1.py for details!

Aron Insinga, W1AKI, 7 December 2023
