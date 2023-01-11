// Free to use, copy, modify or whatever.
// Copyright (c) by Hannu Kotipalo
// Version 1.1
// 1.0-1.1:
//	- To and CC - headers checked

#include <stdio.h>
#define false 0
#define true (!false)
#define bool unsigned short
#define bufsize 1024

char InputLine[bufsize],ReceivedFor[bufsize];
char ToAddress[bufsize],CcAddress[bufsize],TempAddress[bufsize];
char UserName[bufsize];
char DomainName[bufsize];

bool IsEmptyLine(char*line)
{
	while (*line)
	{
		if (*line>' ') return false;
		line++;
	}
	return true;
}

unsigned int FindAt(char* src)
{ // Attention: does not find, if @ is at first char, src[0]
unsigned int i;
	for (i=0; src[i]; i++)
	{
		if (i >= bufsize) return 0;
		if (src[i]=='@') return i;
	}
	return 0;
}

bool IsEmailChar(char c)
{
	return (
	((c>'?') && (c<='~')) ||
	((c>'"') && (c<',')) ||
	((c>',') && (c<';')) ||
	(c=='=') ||
	(c=='!'));
}

char * CopyEmailAddr(char* dest, char* src)
{
unsigned int i,j;
	i = 0;
	j = FindAt(src);
	if (j)
	{
		while (j && src[j] && IsEmailChar(src[j]) ) j--;
		if (!IsEmailChar(src[j])) j++;
		while (IsEmailChar(src[j]))
		{
			if (i++ >= bufsize) break;
			*dest++ = src[j++];
		}
		*dest='\0';
		return &src[j];
	}
	return NULL;
}

void strccpy(char* dest, char* src, char delim)
{
unsigned int i;
	i=0;
	do
	{
		if (i++ >= bufsize) break;
		*dest++ = *src++;
	} while (*src && (*src != delim));
	*dest++ = '\0';
}

char LowerCase(char c)
{
	if ((c >= 'A') &&
	    (c <= 'Z'))
		c |= 0x20;
	return c;
}


bool strsubcmp(char *mainstr, char* substr)
{
	while (*substr)
	{
		if (LowerCase(*mainstr++) != LowerCase(*substr++)) return false;
	}
	return true;
}

#define H_Unknown 0
#define H_Received 1
#define H_Received_for 2
#define H_To 3
#define H_Cc 4

int main(int argc, char **argv)
{
unsigned int state;
char * r_for;
char * linebrowse;
unsigned int i,ULen,DLen;
char * arg;
	ReceivedFor[0] = '\0';
	ToAddress[0] = '\0';
	CcAddress[0] = '\0';
	ULen=0;
	DLen=0;
	if (argc>1)
	{
		arg = argv[1];
		i = FindAt(arg);
		if (arg[i]=='@')
		{
			strncpy(UserName,arg,i);
			strccpy(DomainName,&arg[i+1],' ');
			ULen=strlen(UserName);
			DLen=strlen(DomainName);
		}
		//printf("<Debug: Name: %s Domain: %s>",UserName,DomainName);
		
	}
	state = H_Unknown;
	while (!feof(stdin))
	{
		fgets(InputLine,bufsize,stdin);
		if (IsEmptyLine(InputLine))
		{
			printf("X-RecFor-Recipient: ");
			if (ToAddress[0])
				printf("%s",ToAddress);
			else
			if (CcAddress[0])
				printf("%s",CcAddress);
			else
				printf("%s",ReceivedFor);
			printf("\n\n");
			break;
		}
		printf("%s",InputLine);
		if (InputLine[0]>' ') 
		{ // Enter a header
			if (strncmp("Received:",InputLine,9)==0)
			{
				//printf("<Debug:Found Received-header>\n");
				state = H_Received;
			}
			else
			if (strncmp("To:",InputLine,3)==0)
			{
				//printf("<Debug:Found To-header>\n");
				state = H_To;
			}
			else
			if (strncmp("Cc:",InputLine,3)==0)
			{
				//printf("<Debug:Found Cc-header>\n");
				state = H_Cc;
			}
			else
				state = H_Unknown;
		}
		switch (state)
		{
			case H_Received:
				if (r_for=strstr(InputLine,"for"))
				{
					//printf("<Debug:Found email!>\n");
					r_for+=3;
					if (CopyEmailAddr(ReceivedFor,r_for)==NULL)
						state = H_Received_for;
				}
				break;
			case H_Received_for:
				// check one line for email address
				CopyEmailAddr(ReceivedFor,InputLine);
				state = H_Received;
				break;
			case H_To:
				if (ULen)
				{
					linebrowse = &InputLine[0];
					while (linebrowse = CopyEmailAddr(TempAddress,linebrowse)) 
					{
						i = FindAt(TempAddress);
						if (strsubcmp(TempAddress,UserName))
						{	
							if (strsubcmp(&TempAddress[i+1],DomainName))
							{
								//printf("<Debug:Found email!>\n");
								CopyEmailAddr(ToAddress,TempAddress);
							}
						}
					}
				}
				break;
			case H_Cc:
				if (ULen)
				{
					linebrowse = &InputLine[0];
					while (linebrowse = CopyEmailAddr(TempAddress,linebrowse))
					{
						i = FindAt(TempAddress);
						if (strsubcmp(TempAddress,UserName))
						{
							if (strsubcmp(&TempAddress[i+1],DomainName))
							{
								//printf("<Debug:Found email!>\n");
								CopyEmailAddr(CcAddress,TempAddress);
							}
						}
					}
				}
				break;
				
		}
	}
	while (!feof(stdin))
	{
		InputLine[0]='\0';
		fgets(InputLine,bufsize,stdin);
		printf("%s",InputLine);
	}
	return (0);
}

